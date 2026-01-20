"""
State management for Streamlit UI
"""
import streamlit as st
from typing import Optional
from ..models import ResearchState


def initialize_session_state() -> None:
    """
    Initializes Streamlit session state with default values.
    Creates: research_states, current_query_id, active_research
    """
    if "research_states" not in st.session_state:
        st.session_state.research_states = {}
    
    if "current_query_id" not in st.session_state:
        st.session_state.current_query_id = None
    
    if "active_research" not in st.session_state:
        st.session_state.active_research = None


def get_current_state(query_id: str) -> Optional[ResearchState]:
    """
    Retrieves ResearchState for given query_id from session state.
    
    Args:
        query_id: Unique query identifier
        
    Returns:
        Optional[ResearchState]: State if found, None otherwise
    """
    initialize_session_state()
    return st.session_state.research_states.get(query_id)


def update_state(query_id: str, state: ResearchState) -> None:
    """
    Updates ResearchState in session state and triggers UI rerun.
    
    Args:
        query_id: Unique query identifier
        state: Updated ResearchState instance
    """
    initialize_session_state()
    st.session_state.research_states[query_id] = state
    st.session_state.current_query_id = query_id
    st.session_state.active_research = state


def clear_completed_research() -> None:
    """
    Clears completed research states from session to free memory.
    """
    initialize_session_state()
    
    # Remove completed and failed states older than 1 hour
    import time
    current_time = time.time()
    
    to_remove = []
    for query_id, state in st.session_state.research_states.items():
        if state.status.value in ["completed", "failed", "cancelled"]:
            # Check if older than 1 hour (simplified check)
            to_remove.append(query_id)
    
    for query_id in to_remove:
        del st.session_state.research_states[query_id]
