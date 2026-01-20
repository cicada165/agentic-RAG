"""
Streaming utilities for real-time UI updates
"""
import asyncio
from typing import Callable, AsyncGenerator
from ..models import StreamEvent


async def stream_to_ui(
    query_id: str,
    event_generator: AsyncGenerator[StreamEvent, None],
    update_callback: Callable[[StreamEvent], None]
) -> None:
    """
    Streams events from workflow to UI update callback.
    
    Args:
        query_id: Unique query identifier
        event_generator: Async generator yielding StreamEvent objects
        update_callback: Function to call with each event (updates Streamlit state)
    """
    async for event in event_generator:
        update_callback(event)
        await asyncio.sleep(0.1)  # Prevent UI flooding


def create_stream_callback(query_id: str) -> Callable[[StreamEvent], None]:
    """
    Creates callback function for streaming events to Streamlit.
    
    Args:
        query_id: Unique query identifier
        
    Returns:
        Callable: Callback function that updates session state and triggers rerun
    """
    import streamlit as st
    from ..utils.state_manager import get_current_state, update_state
    from ..models import ResearchState, ResearchStatus, Source
    
    def callback(event: StreamEvent) -> None:
        # Get current state
        state = get_current_state(query_id)
        if state is None:
            # Create new state if it doesn't exist
            state = ResearchState(
                query=event.data.get("query", ""),
                query_id=query_id
            )
        
        # Update state based on event type
        if event.event_type == "status":
            status_str = event.data.get("status", "pending")
            try:
                state.status = ResearchStatus(status_str)
            except ValueError:
                pass
            state.current_agent = event.agent
        
        elif event.event_type == "source":
            source_data = event.data.get("source", {})
            if source_data:
                source = Source(**source_data) if isinstance(source_data, dict) else source_data
                if source not in state.sources:
                    state.sources.append(source)
        
        elif event.event_type == "progress":
            # Update progress information
            pass
        
        elif event.event_type == "report_chunk":
            chunk = event.data.get("chunk", "")
            state.draft_report += chunk
        
        elif event.event_type == "complete":
            state.status = ResearchStatus.COMPLETED
            if "report" in event.data:
                state.final_report = event.data["report"]
        
        elif event.event_type == "error":
            state.status = ResearchStatus.FAILED
            state.error_message = event.data.get("error", "Unknown error")
        
        # Update state
        update_state(query_id, state)
        
        # Note: st.rerun() is not called here to avoid issues in async contexts
        # The main app will periodically check state and rerun as needed
        # This callback is called from async workflow, so we only update state
    
    return callback
