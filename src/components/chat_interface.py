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


def render_status_panel(state: ResearchState) -> None:
    """
    Renders research status panel with progress indicators.
    
    Args:
        state: Current ResearchState instance
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
        "cancelled": "⚫"
    }
    
    status_icon = status_colors.get(status, "⚪")
    st.sidebar.markdown(f"**Status:** {status_icon} {status.title()}")
    
    # Current agent
    if state.current_agent:
        st.sidebar.markdown(f"**Current Agent:** {state.current_agent.title()}")
    
    # Progress metrics
    st.sidebar.markdown("---")
    st.sidebar.metric("Sources Found", len(state.sources))
    st.sidebar.metric("Verified Sources", len(state.verified_sources))
    st.sidebar.metric("Confidence Score", f"{state.confidence_score:.2f}")
    
    # Execution time
    if state.execution_time_seconds:
        st.sidebar.metric("Execution Time", f"{state.execution_time_seconds:.1f}s")
    
    # Search queries
    if state.search_queries:
        st.sidebar.markdown("---")
        st.sidebar.markdown("**Search Queries:**")
        for i, query in enumerate(state.search_queries[:5], 1):
            st.sidebar.text(f"{i}. {query[:50]}..." if len(query) > 50 else f"{i}. {query}")


def render_report_viewer(report: str, citations: List[str]) -> None:
    """
    Renders final report with markdown formatting and citations.
    
    Args:
        report: Markdown-formatted report string
        citations: List of citation URLs
    """
    st.markdown("## Research Report")
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
    st.error(f"❌ Error: {error}")
    st.info("Please try again or check your configuration settings.")
