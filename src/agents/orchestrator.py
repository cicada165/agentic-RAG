"""
LangGraph Orchestrator - Manages research workflow
"""
import asyncio
import uuid
from typing import TypedDict, Optional, Callable
from datetime import datetime

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Fallback if langgraph is not installed
    StateGraph = None
    END = None

from ..models import ResearchState, ResearchStatus, StreamEvent, Source, TokenUsage
from .research_agent import research_node
from .reviewer_agent import review_node
from .writer_agent import write_node
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphState(TypedDict):
    """LangGraph state compatible with ResearchState"""
    query: str
    query_id: str
    status: str
    current_agent: Optional[str]
    iteration_count: int
    max_iterations: int
    sources: list
    search_queries: list
    raw_search_results: list
    verified_sources: list
    conflicting_claims: list
    confidence_score: float
    draft_report: str
    final_report: Optional[str]
    citations: list
    error_message: Optional[str]
    execution_time_seconds: Optional[float]
    usage: dict


def create_research_graph() -> Optional[StateGraph]:
    """
    Creates LangGraph workflow for research pipeline.
    
    Returns:
        StateGraph: Configured graph with nodes and edges:
            - Nodes: research_node, review_node, write_node, error_handler_node
            - Edges: research → review → write → end
            - Conditional edges for error handling
    """
    if StateGraph is None:
        logger.warning("LangGraph not installed. Using fallback workflow.")
        return None
    
    # Create graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("research", research_node)
    workflow.add_node("review", review_node)
    workflow.add_node("write", write_node)
    workflow.add_node("error_handler", _error_handler_node)
    
    # Set entry point
    workflow.set_entry_point("research")
    
    # Add edges
    workflow.add_edge("research", "review")
    workflow.add_edge("write", END)
    
    # Add conditional edge for research -> review (with revision loop)
    workflow.add_conditional_edges(
        "research",
        _should_continue,
        {
            "continue": "review",
            "error": "error_handler"
        }
    )
    
    # Add conditional edge for review -> write or research (revision loop)
    workflow.add_conditional_edges(
        "review",
        _review_decision,
        {
            "continue": "write",
            "needs_revision": "research",  # Loop back to research
            "error": "error_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "write",
        _should_continue,
        {
            "continue": END,
            "error": "error_handler"
        }
    )
    
    workflow.add_edge("error_handler", END)
    
    return workflow.compile()


def _should_continue(state: GraphState) -> str:
    """Determine if workflow should continue or handle error"""
    status = state.get("status", "")
    if status == ResearchStatus.FAILED.value:
        return "error"
    return "continue"


def _review_decision(state: GraphState) -> str:
    """
    Determine next step after review node.
    Returns 'needs_revision' to loop back to research, 'continue' to proceed to write, or 'error' for failures.
    """
    status = state.get("status", "")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    
    # Check for failures
    if status == ResearchStatus.FAILED.value:
        return "error"
    
    # Check if revision is needed
    if status == ResearchStatus.NEEDS_REVISION.value:
        # Check if we've exceeded max iterations
        if iteration_count >= max_iterations:
            logger.warning(f"Max iterations ({max_iterations}) reached. Proceeding to write despite low quality.")
            return "continue"
        logger.info(f"Revision needed (iteration {iteration_count}/{max_iterations}). Looping back to research.")
        return "needs_revision"
    
    # Otherwise continue to write
    return "continue"


def _error_handler_node(state: dict) -> dict:
    """Handle errors in the workflow"""
    logger.error(f"Workflow error: {state.get('error_message', 'Unknown error')}")
    state["status"] = ResearchStatus.FAILED.value
    return state


async def run_research_workflow(
    query: str,
    query_id: str,
    stream_callback: Optional[Callable[[StreamEvent], None]] = None
) -> ResearchState:
    """
    Executes research workflow asynchronously.
    
    Args:
        query: User research query
        query_id: Unique identifier for this research session
        stream_callback: Optional callback function for streaming events to UI
        
    Returns:
        ResearchState: Final state after workflow completion
        
    Raises:
        ResearchException: If workflow fails irrecoverably
    """
    from ..utils.exceptions import ResearchException
    
    start_time = datetime.now()
    
    # Initialize state
    initial_state: GraphState = {
        "query": query,
        "query_id": query_id,
        "status": ResearchStatus.PENDING.value,
        "current_agent": None,
        "iteration_count": 0,
        "max_iterations": 5,
        "sources": [],
        "search_queries": [],
        "raw_search_results": [],
        "verified_sources": [],
        "conflicting_claims": [],
        "confidence_score": 0.0,
        "draft_report": "",
        "final_report": None,
        "citations": [],
        "error_message": None,
        "execution_time_seconds": None,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "estimated_cost_usd": 0.0}
    }
    
    # Emit initial status
    if stream_callback:
        event = StreamEvent(
            event_type="status",
            query_id=query_id,
            agent=None,
            data={"status": "pending", "message": "Starting research..."}
        )
        stream_callback(event)
    
    try:
        # Create and run workflow
        graph = create_research_graph()
        
        if graph is None:
            # Fallback: run nodes sequentially without LangGraph (with revision loop support)
            logger.info("Running workflow without LangGraph (fallback mode)")
            state = initial_state
            
            # Loop until completion or max iterations
            max_iterations = state.get("max_iterations", 5)
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                state["iteration_count"] = iteration
                
                # Emit status
                if stream_callback:
                    event = StreamEvent(
                        event_type="status",
                        query_id=query_id,
                        agent="research",
                        data={"status": "researching", "message": f"Gathering sources... (iteration {iteration}/{max_iterations})"}
                    )
                    stream_callback(event)
                
                # Run research
                state = await research_node(state)
                
                # Emit sources as they're found
                if stream_callback and state.get("sources"):
                    for source_dict in state.get("sources", [])[:5]:  # Emit first 5
                        event = StreamEvent(
                            event_type="source",
                            query_id=query_id,
                            agent="research",
                            data={"source": source_dict}
                        )
                        stream_callback(event)
                
                # Emit status
                if stream_callback:
                    event = StreamEvent(
                        event_type="status",
                        query_id=query_id,
                        agent="reviewer",
                        data={"status": "reviewing", "message": "Verifying sources..."}
                    )
                    stream_callback(event)
                
                # Run review
                state = await review_node(state)
                
                # Check if revision is needed
                if state.get("status") == ResearchStatus.NEEDS_REVISION.value:
                    logger.info(f"Revision needed. Looping back to research (iteration {iteration}/{max_iterations})")
                    if stream_callback:
                        event = StreamEvent(
                            event_type="status",
                            query_id=query_id,
                            agent="reviewer",
                            data={"status": "needs_revision", "message": state.get("error_message", "Insufficient sources. Retrying...")}
                        )
                        stream_callback(event)
                    # Continue loop to research again
                    continue
                
                # If review passed, break and proceed to write
                break
            
            # Emit status
            if stream_callback:
                event = StreamEvent(
                    event_type="status",
                    query_id=query_id,
                    agent="writer",
                    data={"status": "writing", "message": "Generating report..."}
                )
                stream_callback(event)
            
            # Run write
            state = await write_node(state)
            
            # Emit completion
            if stream_callback:
                event = StreamEvent(
                    event_type="complete",
                    query_id=query_id,
                    agent=None,
                    data={"status": "completed", "report": state.get("final_report")}
                )
                stream_callback(event)
        else:
            # Run with LangGraph
            final_state = await graph.ainvoke(initial_state)
            state = final_state
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        state["execution_time_seconds"] = execution_time
        
        # Convert to ResearchState
        research_state = ResearchState(
            query=state["query"],
            query_id=state["query_id"],
            status=ResearchStatus(state["status"]),
            current_agent=state.get("current_agent"),
            iteration_count=state.get("iteration_count", 0),
            max_iterations=state.get("max_iterations", 5),
            sources=[Source(**s) if isinstance(s, dict) else s for s in state.get("sources", [])],
            search_queries=state.get("search_queries", []),
            raw_search_results=state.get("raw_search_results", []),
            verified_sources=[Source(**s) if isinstance(s, dict) else s for s in state.get("verified_sources", [])],
            conflicting_claims=state.get("conflicting_claims", []),
            confidence_score=state.get("confidence_score", 0.0),
            draft_report=state.get("draft_report", ""),
            final_report=state.get("final_report"),
            citations=state.get("citations", []),
            error_message=state.get("error_message"),
            execution_time_seconds=execution_time,
            usage=TokenUsage(**state.get("usage", {})) if state.get("usage") else TokenUsage()
        )
        
        return research_state
        
    except Exception as e:
        logger.error(f"Workflow failed: {e}")
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Emit error
        if stream_callback:
            event = StreamEvent(
                event_type="error",
                query_id=query_id,
                agent=None,
                data={"error": str(e)}
            )
            stream_callback(event)
        
        raise ResearchException(f"Research workflow failed: {str(e)}")
