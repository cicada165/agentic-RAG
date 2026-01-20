"""
Writer Agent - Generates final markdown report with citations
"""
from typing import List, Optional, Any, Tuple
from ..models import Source, WriterAgentResponse
from ..utils.config import Config
from ..utils.exceptions import LLMException
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


async def generate_report(
    query: str,
    verified_sources: List[Source],
    conflicts: Optional[List[str]] = None,
    llm_client: Optional[Any] = None
) -> Tuple[str, List[str]]:
    """
    Generates markdown report from verified sources.
    
    Args:
        query: Original research query
        verified_sources: List of verified sources
        conflicts: Optional list of conflicts to address
        llm_client: LLM client instance
        
    Returns:
        tuple[str, List[str]]: (markdown_report, citations)
            - markdown_report: Complete markdown-formatted report
            - citations: List of citation URLs in order of appearance
    """
    if not verified_sources:
        return "# Research Report\n\nNo verified sources found for this query.", []
    
    # Generate report structure
    report_parts = [
        f"# Research Report: {query}\n\n",
        "## Summary\n\n",
        f"This report synthesizes information from {len(verified_sources)} verified sources.\n\n"
    ]
    
    # Add main content from sources
    report_parts.append("## Key Findings\n\n")
    
    citations = []
    for i, source in enumerate(verified_sources, 1):
        citations.append(source.url)
        report_parts.append(f"### Finding {i}\n\n")
        report_parts.append(f"{source.snippet}\n\n")
        report_parts.append(f"*Source: [{source.title}]({source.url})*\n\n")
    
    # Add conflicts section if any
    if conflicts:
        report_parts.append("## Conflicting Information\n\n")
        for conflict in conflicts:
            report_parts.append(f"- {conflict}\n")
        report_parts.append("\n")
    
    # Add references section
    report_parts.append("## References\n\n")
    for i, source in enumerate(verified_sources, 1):
        report_parts.append(f"{i}. [{source.title}]({source.url})\n")
    
    report = "".join(report_parts)
    
    return report, citations


def format_citations(
    report: str,
    sources: List[Source]
) -> str:
    """
    Adds citation markers and reference section to report.
    
    Args:
        report: Report text without citations
        sources: List of sources to cite
        
    Returns:
        str: Report with citation markers and references section
    """
    # Citations are already included in generate_report
    # This function can be used for additional formatting if needed
    return report


async def write_node(state: dict) -> dict:
    """
    LangGraph node function for writing phase.
    Generates final markdown report with citations.
    
    Args:
        state: Current graph state with verified sources
        
    Returns:
        dict: Updated state with final report
    """
    from ..models import ResearchStatus, Source
    
    logger.info("Starting writing phase")
    
    try:
        # Update status
        state["status"] = ResearchStatus.WRITING.value
        state["current_agent"] = "writer"
        
        # Convert verified sources from dict to Source objects
        verified_dicts = state.get("verified_sources", [])
        verified_sources = [Source(**s) if isinstance(s, dict) else s for s in verified_dicts]
        
        query = state.get("query", "")
        conflicts = state.get("conflicting_claims", [])
        
        # Generate report
        report, citations = await generate_report(
            query,
            verified_sources,
            conflicts if conflicts else None
        )
        
        # Format citations
        final_report = format_citations(report, verified_sources)
        
        # Update state
        state["draft_report"] = report
        state["final_report"] = final_report
        state["citations"] = citations
        state["status"] = ResearchStatus.COMPLETED.value
        
        logger.info("Writing completed. Report generated.")
        
    except Exception as e:
        logger.error(f"Writing failed: {e}")
        state["status"] = ResearchStatus.FAILED.value
        state["error_message"] = str(e)
    
    return state
