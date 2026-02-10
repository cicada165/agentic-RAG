"""
Main Streamlit application entry point for Deep Research Assistant
"""
import asyncio
import uuid
import threading
import time
import streamlit as st
from typing import Optional

from .models import ResearchState, ResearchStatus
from .agents.orchestrator import run_research_workflow
from .components.chat_interface import (
    render_chat_input,
    render_message_history,
    render_status_panel,
    render_report_viewer,
    render_error_message
)
from .utils.state_manager import (
    initialize_session_state,
    get_current_state,
    update_state,
    clear_completed_research
)
from .utils.streaming import create_stream_callback
from .utils.config import Config, ConfigError
from .utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    """
    Main Streamlit application entry point.
    Initializes session state and renders UI components.
    """
    st.set_page_config(
        page_title="Deep Research Assistant",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Deep Research Assistant")
    st.markdown("Ask a research question and get a comprehensive, fact-checked report with citations.")
    
    # Initialize session state
    initialize_session_state()
    
    # Load configuration
    try:
        config = Config.load()
        st.sidebar.success("✅ Configuration loaded")
    except ConfigError as e:
        st.sidebar.error(f"❌ Configuration error: {str(e)}")
        st.info("Please set your API keys in `.env` file or Streamlit secrets.")
        return
    
    # Sidebar configuration
    with st.sidebar:
        st.header("Settings")
        max_sources = st.slider("Max Sources", 5, 30, config.MAX_SOURCES_PER_QUERY)
        min_relevance = st.slider("Min Relevance Score", 0.0, 1.0, config.MIN_RELEVANCE_SCORE, 0.1)
        
        if st.button("Clear Completed Research"):
            clear_completed_research()
            st.success("Cleared completed research")
    
    # Chat input
    query = render_chat_input()
    
    # Handle new query
    if query:
        if not query.strip():
            st.warning("Please enter a non-empty query.")
            return
        
        # Generate unique query ID
        query_id = str(uuid.uuid4())
        
        # Create initial state
        initial_state = ResearchState(
            query=query,
            query_id=query_id,
            status=ResearchStatus.PENDING
        )
        update_state(query_id, initial_state)
        
        # Create stream callback
        stream_callback = create_stream_callback(query_id)
        
        # Check if there's already a running task for this query
        task_key = f"research_task_{query_id}"
        task_status = st.session_state.get(task_key, "not_started")
        
        if task_status == "not_started":
            # Mark task as running
            st.session_state[task_key] = "running"
            
            # Run async workflow in background thread to avoid blocking UI
            
            def run_async_workflow():
                """Run the async workflow in a separate event loop"""
                try:
                    # Create new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    
                    # Run the async workflow
                    final_state = new_loop.run_until_complete(
                        run_research_workflow(
                            query=query,
                            query_id=query_id,
                            stream_callback=stream_callback
                        )
                    )
                    
                    # Update final state (thread-safe via session state)
                    # Use a fresh get_current_state to avoid overwriting updates made by main thread
                    # (like cancellation)
                    # However, strictly speaking, we are in a different thread.
                    # We should check if cancelled before writing.
                    # But since st.session_state is thread-safe wrapper, we can just write.
                    # To be safe, check status.
                    current_final = get_current_state(query_id)
                    if current_final and current_final.status == ResearchStatus.CANCELLED:
                        logger.info("Research cancelled, ignoring final state update from thread.")
                    else:
                        update_state(query_id, final_state)
                        st.session_state[task_key] = "completed"
                    
                    new_loop.close()
                except Exception as e:
                    logger.error(f"Research failed: {e}")
                    state = get_current_state(query_id)
                    if state:
                        state.status = ResearchStatus.FAILED
                        state.error_message = str(e)
                        update_state(query_id, state)
                    st.session_state[task_key] = "failed"
                    if 'new_loop' in locals():
                        new_loop.close()
            
            # Start background thread
            thread = threading.Thread(target=run_async_workflow, daemon=True)
            thread.start()
            
            # Show initial spinner
            with st.spinner("Starting research..."):
                # Small delay to allow thread to start
                time.sleep(0.1)
        
        # Check task status and handle accordingly
        elif task_status == "running":
            # Show progress indicator
            st.info("🔍 Research in progress... This may take a moment.")
            # Trigger rerun to check status again (Streamlit will handle this)
            # Use a small delay to prevent excessive reruns
            time.sleep(0.5)
            st.rerun()
        
        elif task_status == "completed":
            # Clean up task status and show results
            del st.session_state[task_key]
            # State is already updated, just rerun to show results
            st.rerun()
        
        elif task_status == "failed":
            # Clean up task status and show error
            del st.session_state[task_key]
            state = get_current_state(query_id)
            if state and state.error_message:
                render_error_message(state.error_message)
                
        elif task_status == "cancelled":
             # Clean up task status
             del st.session_state[task_key]
             st.rerun()
    
    # Display current research state
    current_query_id = st.session_state.get("current_query_id")
    if current_query_id:
        state = get_current_state(current_query_id)
        
        if state:
            # Render status panel and check for stop
            stop_clicked = render_status_panel(state)
            
            if stop_clicked:
                # Handle cancellation
                state.status = ResearchStatus.CANCELLED
                update_state(current_query_id, state)
                
                # Mark task as cancelled
                task_key = f"research_task_{current_query_id}"
                if task_key in st.session_state:
                    st.session_state[task_key] = "cancelled"
                
                st.rerun()
            
            # Main content area
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Show query
                st.markdown(f"### Query: {state.query}")
                
                # Show sources if available
                if state.sources:
                    with st.expander(f"Sources ({len(state.sources)})", expanded=False):
                        for i, source in enumerate(state.sources, 1):
                            st.markdown(f"**{i}. [{source.title}]({source.url})**")
                            st.caption(f"Relevance: {source.relevance_score:.2f} | Verified: {'✅' if source.verified else '❌'}")
                            st.text(source.snippet[:200] + "..." if len(source.snippet) > 200 else source.snippet)
                            st.markdown("---")
                
                # Show report if available
                if state.final_report:
                    render_report_viewer(state.final_report, state.citations)
                elif state.draft_report:
                    st.markdown("### Draft Report")
                    st.markdown(state.draft_report)
                elif state.status == ResearchStatus.RESEARCHING:
                    st.info("🔍 Researching... Gathering sources from the web.")
                elif state.status == ResearchStatus.REVIEWING:
                    st.info("🔍 Reviewing... Verifying sources and checking for conflicts.")
                elif state.status == ResearchStatus.WRITING:
                    st.info("✍️ Writing... Generating final report.")
                elif state.status == ResearchStatus.FAILED:
                    if state.error_message:
                        render_error_message(state.error_message)
                elif state.status == ResearchStatus.CANCELLED:
                    st.warning("🛑 Research cancelled by user.")
                elif state.status == ResearchStatus.NEEDS_REVISION:
                    st.info(f"🔄 Revision needed: {state.error_message or 'Improving research quality...'}")
                
                # Show conflicts if any
                if state.conflicting_claims:
                    with st.expander("⚠️ Conflicting Claims Detected", expanded=True):
                        for conflict in state.conflicting_claims:
                            st.warning(conflict)
            
            with col2:
                # Show verified sources
                if state.verified_sources:
                    st.markdown("### Verified Sources")
                    for source in state.verified_sources[:10]:
                        st.markdown(f"- [{source.title}]({source.url})")
    
    # Show message history (if implemented)
    # messages = st.session_state.get("messages", [])
    # if messages:
    #     render_message_history(messages)


if __name__ == "__main__":
    main()
