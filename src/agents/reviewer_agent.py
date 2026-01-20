"""
Reviewer Agent - Fact-checks sources and identifies conflicts
"""
from typing import List, Optional, Any, Tuple
from ..models import Source, ReviewerAgentResponse
from ..utils.config import Config
from ..utils.exceptions import LLMException
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


async def verify_source(
    source: Source,
    query: str,
    llm_client: Optional[Any] = None
) -> Tuple[bool, float]:
    """
    Verifies a single source for factual accuracy and relevance using LLM.
    
    Args:
        source: Source to verify
        query: Original research query
        llm_client: LLM client instance (required for intelligent verification)
        
    Returns:
        tuple[bool, float]: (is_verified, confidence_score)
            - is_verified: Whether source passes verification
            - confidence_score: Confidence level 0.0-1.0
    """
    # 1. HARD FILTER: Garbage Snippets
    if not source.snippet or len(source.snippet) < 50:  # Increased threshold from 20 to 50
        return False, 0.0
    
    if not source.url or not source.title:
        return False, 0.0
    
    # 2. INTELLIGENT FILTER: Ask the LLM
    # If we are in "Mock" mode or no client, fallback to math
    if not llm_client:
        # Fallback to relevance score check
        return source.relevance_score > 0.4, source.relevance_score
    
    # Use LLM to verify if snippet actually answers the query
    prompt = f"""Verify if this text answers the query: "{query}"
Text: "{source.snippet}"

Return YES only if the text contains specific facts/data. Return NO if it is generic SEO spam."""

    try:
        response = await llm_client.ainvoke(prompt)  # Async call
        content = response.content if hasattr(response, 'content') else str(response)
        is_valid = "YES" in content.upper()
        return is_valid, 0.9 if is_valid else 0.1
    except Exception as e:
        logger.warning(f"LLM verification failed: {e}. Falling back to relevance score.")
        # Fallback to relevance score if LLM fails
        return source.relevance_score > 0.4, source.relevance_score


async def detect_conflicts(
    sources: List[Source],
    query: str,
    llm_client: Optional[Any] = None
) -> List[str]:
    """
    Detects conflicting claims across sources.
    
    Args:
        sources: List of sources to analyze
        query: Original research query
        llm_client: LLM client instance
        
    Returns:
        List[str]: List of conflicting claim descriptions
    """
    # Simple conflict detection (can be enhanced with LLM)
    conflicts = []
    
    if len(sources) < 2:
        return conflicts
    
    # Check for contradictory keywords in snippets
    # This is a simplified version - real implementation would use LLM
    key_terms = set()
    for source in sources:
        words = source.snippet.lower().split()
        key_terms.update(words[:10])  # First 10 words
    
    # If sources have very different key terms, might indicate conflict
    # This is a placeholder - real conflict detection needs semantic analysis
    
    return conflicts


def calculate_confidence_score(
    verified_sources: List[Source],
    conflicts: List[str]
) -> float:
    """
    Calculates overall confidence score for research.
    
    Args:
        verified_sources: List of verified sources
        conflicts: List of detected conflicts
        
    Returns:
        float: Confidence score between 0.0 and 1.0
    """
    if not verified_sources:
        return 0.0
    
    # Base score from number of verified sources
    source_count_score = min(len(verified_sources) / 10.0, 1.0)
    
    # Penalty for conflicts
    conflict_penalty = min(len(conflicts) * 0.1, 0.5)
    
    # Average relevance score
    avg_relevance = sum(s.relevance_score for s in verified_sources) / len(verified_sources)
    
    # Combined score
    confidence = (source_count_score * 0.3 + avg_relevance * 0.7) - conflict_penalty
    
    return max(0.0, min(1.0, confidence))


async def review_node(state: dict) -> dict:
    """
    LangGraph node function for review phase.
    Fact-checks sources and identifies conflicts.
    
    Args:
        state: Current graph state with sources
        
    Returns:
        dict: Updated state with verified sources and confidence
    """
    from ..models import ResearchStatus, Source
    
    logger.info("Starting review phase")
    
    try:
        # Update status
        state["status"] = ResearchStatus.REVIEWING.value
        state["current_agent"] = "reviewer"
        
        # Convert sources from dict to Source objects
        source_dicts = state.get("sources", [])
        sources = [Source(**s) if isinstance(s, dict) else s for s in source_dicts]
        
        query = state.get("query", "")
        
        # Load LLM client for intelligent verification
        from ..utils.llm_client import create_llm_client
        try:
            llm_client = create_llm_client()
        except Exception as e:
            logger.warning(f"Could not create LLM client for verification: {e}. Using fallback verification.")
            llm_client = None
        
        # Verify each source with LLM
        verified_sources = []
        for source in sources:
            is_verified, confidence = await verify_source(source, query, llm_client=llm_client)
            if is_verified:
                source.verified = True
                verified_sources.append(source)
        
        # Detect conflicts
        conflicts = await detect_conflicts(verified_sources, query)
        
        # Calculate overall confidence
        confidence_score = calculate_confidence_score(verified_sources, conflicts)
        
        # QUALITY CHECK: If insufficient verified sources, trigger revision loop
        min_verified_sources = 2  # Minimum required verified sources
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 5)
        
        if len(verified_sources) < min_verified_sources:
            # Check if we've exceeded max iterations
            if iteration_count >= max_iterations:
                logger.warning(f"Max iterations reached ({max_iterations}). Proceeding with {len(verified_sources)} sources.")
                # Continue anyway if max iterations reached
            else:
                logger.warning(f"Quality check failed. Verified sources: {len(verified_sources)}/{min_verified_sources}. Triggering revision.")
                
                return {
                    **state,  # Preserve existing state (query, id, etc.)
                    "status": ResearchStatus.NEEDS_REVISION.value,
                    "iteration_count": iteration_count + 1,
                    "error_message": f"Insufficient verified sources (found {len(verified_sources)}/{min_verified_sources}). Try broader search terms.",
                    "sources": [],  # Clear bad sources so Researcher starts fresh
                    "search_queries": [],  # Clear old queries to force generation of new ones
                    "current_agent": "reviewer",
                    "verified_sources": [],  # Clear verified sources
                    "conflicting_claims": [],
                    "confidence_score": 0.0
                }
        
        # Update state with successful review
        state["verified_sources"] = [s.model_dump() for s in verified_sources]
        state["conflicting_claims"] = conflicts
        state["confidence_score"] = confidence_score
        state["status"] = ResearchStatus.REVIEWING.value  # Will be updated to next status by orchestrator
        
        logger.info(f"Review completed. Verified {len(verified_sources)} sources. Confidence: {confidence_score:.2f}")
        
    except Exception as e:
        logger.error(f"Review failed: {e}")
        state["status"] = ResearchStatus.FAILED.value
        state["error_message"] = str(e)
    
    return state
