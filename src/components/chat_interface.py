"""
Streamlit UI components for chat interface
"""
import streamlit as st
from typing import List, Optional
from ..models import ResearchState


def render_chat_input() -> Optional[str]:
    """
    Renders chat input widget.
    
    Returns:
        Optional[str]: User query if submitted, None otherwise
    """
    query = st.chat_input("Enter your research query...")
    return query


def render_message_history(messages: List[dict]) -> None:
    """
    Renders chat message history.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
    """
    for message in messages:
        with st.chat_message(message.get("role", "user")):
            st.markdown(message.get("content", ""))


def render_status_panel(state: ResearchState) -> bool:
    """
    Renders research status panel with progress indicators.
    
    Args:
        state: Current ResearchState instance
        
    Returns:
        bool: True if 'Stop Research' button was clicked, False otherwise
    """
    st.sidebar.header("Research Status")
    
    # Status indicator
    status = state.status.value
    status_colors = {
        "pending": "⚪",
        "researching": "🔵",
        "reviewing": "🟡",
        "writing": "🟠",
        "completed": "🟢",
        "failed": "🔴",
        "cancelled": "⚫",
        "needs_revision": "🟣"
    }
    
    # Calculate progress
    progress_map = {
        "pending": 0,
        "researching": 25,
        "needs_revision": 35,
        "reviewing": 60,
        "writing": 90,
        "completed": 100,
        "failed": 100,
        "cancelled": 100
    }
    progress = progress_map.get(status, 0)
    
    status_icon = status_colors.get(status, "⚪")
    st.sidebar.markdown(f"**Status:** {status_icon} {status.replace('_', ' ').title()}")
    st.sidebar.progress(progress / 100)
    
    # Current agent
    if state.current_agent:
        st.sidebar.markdown(f"**Current Agent:** {state.current_agent.title()}")
        
    # Stop button for active states
    stop_clicked = False
    if status in ["researching", "reviewing", "writing", "pending", "needs_revision"]:
        if st.sidebar.button("Stop Research", type="primary"):
            stop_clicked = True
    
    # Progress metrics
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Sources", len(state.sources))
        st.metric("Confidence", f"{state.confidence_score:.2f}")
    with col2:
        st.metric("Verified", len(state.verified_sources))
        st.metric("Iteration", f"{state.iteration_count}/{state.max_iterations}")
    
    # Execution time
    if state.execution_time_seconds:
        st.sidebar.metric("Time", f"{state.execution_time_seconds:.1f}s")
    
    # Search queries
    if state.search_queries:
        st.sidebar.markdown("---")
        with st.sidebar.expander("Search Queries", expanded=False):
            for i, query in enumerate(state.search_queries, 1):
                st.text(f"{i}. {query}")
                
    return stop_clicked


def render_report_viewer(report: str, citations: List[str]) -> None:
    """
    Renders final report with markdown formatting and citations.
    
    Args:
        report: Markdown-formatted report string
        citations: List of citation URLs
    """
    st.markdown("## Research Report")
    
    # Add download button
    st.download_button(
        label="Download Report",
        data=report,
        file_name="research_report.md",
        mime="text/markdown"
    )
    
    st.markdown(report)
    
    if citations:
        st.markdown("---")
        st.markdown("### Citations")
        for i, citation in enumerate(citations, 1):
            st.markdown(f"{i}. [{citation}]({citation})")


def render_error_message(error: str) -> None:
    """
    Renders user-friendly error message.
    
    Args:
        error: Error message string
    """
    with st.container():
        st.error(f"❌ **Research Failed**")
        st.markdown(f"**Error Details:** {error}")
        st.info("💡 **Suggestion:** Try rephrasing your query or checking your API keys in `.env`.")
