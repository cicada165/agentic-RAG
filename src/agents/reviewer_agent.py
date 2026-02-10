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
) -> Tuple[bool, float, Any]:
    """
    Verifies a single source for factual accuracy and relevance using LLM.
    
    Args:
        source: Source to verify
        query: Original research query
        llm_client: LLM client instance (required for intelligent verification)
        
    Returns:
        tuple[bool, float, TokenUsage]: (is_verified, confidence_score, token_usage)
            - is_verified: Whether source passes verification
            - confidence_score: Confidence level 0.0-1.0
            - token_usage: Usage for this call
    """
    from ..models import TokenUsage
    from ..utils.monitoring import UsageTracker
    from ..utils.config import Config
    
    # 1. HARD FILTER: Garbage Snippets
    config = Config.load()
    if not source.snippet or len(source.snippet) < config.MIN_SOURCE_SNIPPET_LENGTH:
        return False, 0.0, TokenUsage()
    
    if not source.url or not source.title:
        return False, 0.0, TokenUsage()
    
    # 2. INTELLIGENT FILTER: Ask the LLM
    # If we are in "Mock" mode or no client, fallback to math
    if not llm_client:
        # Fallback to relevance score check
        return source.relevance_score > config.VERIFICATION_FALLBACK_RELEVANCE, source.relevance_score, TokenUsage()
    
    # Use LLM to verify if snippet actually answers the query
    prompt = f"""Verify if this text answers the query: "{query}"
Text: "{source.snippet}"

Return YES only if the text contains specific facts/data. Return NO if it is generic SEO spam."""

    try:
        response = await llm_client.ainvoke(prompt)  # Async call
        
        # Extract usage
        config = Config.load()
        usage = UsageTracker.extract_usage(response, config.LLM_MODEL)
        
        content = response.content if hasattr(response, 'content') else str(response)
        is_valid = "YES" in content.upper()
        return is_valid, 0.9 if is_valid else 0.1, usage
    except Exception as e:
        logger.warning(f"LLM verification failed: {e}. Falling back to relevance score.")
        # Fallback to relevance score if LLM fails
        return source.relevance_score > config.VERIFICATION_FALLBACK_RELEVANCE, source.relevance_score, TokenUsage()


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


async def verify_sources_batch(
    sources: List[Source],
    query: str,
    llm_client: Optional[Any] = None
) -> Tuple[List[Tuple[bool, float]], Any]:
    """
    Verifies multiple sources in a batch using LLM to reduce API calls.
    Uses caching to avoid re-verifying known sources.
    
    Args:
        sources: List of sources to verify
        query: Original research query
        llm_client: LLM client instance
        
    Returns:
        tuple[List[Tuple[bool, float]], TokenUsage]: 
            (List of (is_verified, confidence) tuples, token_usage)
    """
    from ..utils.cache import VerificationCache
    from ..models import TokenUsage
    from ..utils.monitoring import UsageTracker
    
    cache = VerificationCache()
    
    results: List[Optional[Tuple[bool, float]]] = [None] * len(sources)
    total_usage = TokenUsage()
    
    # 1. Check Cache First
    uncached_indices = []
    uncached_sources = []
    
    for i, source in enumerate(sources):
        if not source.url: # Can't cache without URL
            results[i] = (False, 0.0)
            continue
            
        cached_result = cache.get(query, source.url)
        if cached_result:
            results[i] = cached_result
        else:
            uncached_indices.append(i)
            uncached_sources.append(source)
            
    # If all were cached, return immediately!
    if not uncached_indices:
        return [r for r in results if r is not None], total_usage
        
    # 2. Process Uncached Sources (Same logic as before, but only for uncached)
    
    # If no LLM client, fallback to simple relevance check for all uncached
    if not llm_client:
        for i, source in enumerate(uncached_sources):
            original_idx = uncached_indices[i]
            # Hard filter first
            config = Config.load()
            if not source.snippet or len(source.snippet) < config.MIN_SOURCE_SNIPPET_LENGTH:
                 res = (False, 0.0)
            else:
                 res = (source.relevance_score > config.VERIFICATION_FALLBACK_RELEVANCE, source.relevance_score)
            
            results[original_idx] = res
            if source.url:
                cache.set(query, source.url, res)
        return [r for r in results if r is not None], total_usage

    # Filter out obvious garbage from uncached sources
    valid_batch_indices = [] # Indices into uncached_sources/uncached_indices
    clean_sources = []
    
    config = Config.load()
    for i, source in enumerate(uncached_sources):
        original_idx = uncached_indices[i]
        if not source.snippet or len(source.snippet) < config.MIN_SOURCE_SNIPPET_LENGTH:
             res = (False, 0.0)
             results[original_idx] = res
             if source.url:
                cache.set(query, source.url, res)
        else:
            valid_batch_indices.append(i)
            clean_sources.append(source)
            
    if not clean_sources:
        return [r for r in results if r is not None], total_usage

    # Construct batch prompt for remaining clean sources
    sources_text = ""
    for i, source in enumerate(clean_sources):
        sources_text += f"\nSOURCE {i+1}:\n{source.snippet}\n"
        
    prompt = f"""Verify if the following sources answer the query: "{query}"

{sources_text}

For each source, determine if it contains specific facts/data (VALID) or is generic SEO spam (INVALID).
Return a JSON list of objects with 'id' (1-based index) and 'valid' (boolean).
Example: [{{"id": 1, "valid": true}}, {{"id": 2, "valid": false}}]
"""

    try:
        response = await llm_client.ainvoke(prompt)
        
        # Extract usage
        config = Config.load()
        usage = UsageTracker.extract_usage(response, config.LLM_MODEL)
        total_usage = total_usage + usage
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        import json
        batch_results = json.loads(content.strip())
        
        # Map back to results
        result_map = {item['id']: item['valid'] for item in batch_results if 'id' in item and 'valid' in item}
        
        for i, batch_idx in enumerate(valid_batch_indices):
            # source index in batch is i+1
            is_valid = result_map.get(i+1, False)
            res = (is_valid, 0.9 if is_valid else 0.1)
            
            # Map back to original sources list
            original_idx = uncached_indices[batch_idx]
            results[original_idx] = res
            
            # Update cache
            source = clean_sources[i]
            if source.url:
                cache.set(query, source.url, res)
            
    except Exception as e:
        logger.warning(f"Batch verification failed: {e}. Falling back to individual verification.")
        # Fallback to individual verification for clean sources
        for i, batch_idx in enumerate(valid_batch_indices):
            original_idx = uncached_indices[batch_idx]
            is_valid, confidence, usage = await verify_source(clean_sources[i], query, llm_client)
            total_usage = total_usage + usage
            res = (is_valid, confidence)
            results[original_idx] = res
            
            # Check source url before caching
            source = clean_sources[i]
            if source.url:
                cache.set(query, source.url, res)
            
    return [r for r in results if r is not None], total_usage


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
        
        # Batch verify sources
        logger.info(f"Verifying {len(sources)} sources in batch...")
        verification_results, usage = await verify_sources_batch(sources, query, llm_client)
        
        # Track usage
        if "usage" not in state or state["usage"] is None:
            from ..models import TokenUsage
            state["usage"] = TokenUsage().model_dump()
            
        current_usage = state["usage"]
        current_usage["prompt_tokens"] = current_usage.get("prompt_tokens", 0) + usage.prompt_tokens
        current_usage["completion_tokens"] = current_usage.get("completion_tokens", 0) + usage.completion_tokens
        current_usage["total_tokens"] = current_usage.get("total_tokens", 0) + usage.total_tokens
        current_usage["estimated_cost_usd"] = current_usage.get("estimated_cost_usd", 0.0) + usage.estimated_cost_usd
        state["usage"] = current_usage
        
        verified_sources = []
        for i, (is_verified, _) in enumerate(verification_results):
            if is_verified:
                sources[i].verified = True
                verified_sources.append(sources[i])
        
        # Detect conflicts
        conflicts = await detect_conflicts(verified_sources, query)
        
        # Calculate overall confidence
        confidence_score = calculate_confidence_score(verified_sources, conflicts)
        
        # QUALITY CHECK: If insufficient verified sources, trigger revision loop
        config = Config.load()
        min_verified_sources = config.MIN_VERIFIED_SOURCES
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 5)
        
        if len(verified_sources) < min_verified_sources:
            # Check if we've exceeded max iterations
            if iteration_count >= max_iterations:
                msg = f"Max iterations reached ({max_iterations}). Proceeding with {len(verified_sources)} verified sources."
                logger.warning(msg)
                # Continue anyway if max iterations reached
            else:
                msg = f"Quality check failed. Verified sources: {len(verified_sources)}/{min_verified_sources}. Found {len(sources)} total sources. Triggering revision."
                logger.warning(msg)
                
                return {
                    **state,  # Preserve existing state (query, id, etc.)
                    "status": ResearchStatus.NEEDS_REVISION.value,
                    "iteration_count": iteration_count + 1,
                    "error_message": msg,
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
