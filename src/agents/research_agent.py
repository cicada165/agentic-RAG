"""
Research Agent - Performs web search and collects sources
"""
import asyncio
import aiohttp
from typing import List, Optional, Any, Tuple
from datetime import datetime

from ..models import Source, ResearchAgentResponse
from ..utils.config import Config
from ..utils.exceptions import SearchAPIException, LLMException
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


async def generate_search_queries(
    query: str,
    context: Optional[str] = None,  # Changed to str to accept error messages
    max_queries: int = 5,
    llm_client: Optional[Any] = None
) -> Tuple[List[str], Any]:
    """
    Generates optimized search queries from user query.
    
    Args:
        query: Original user query
        context: Optional context/error message from previous attempts (str)
        max_queries: Maximum number of queries to generate
        llm_client: LLM client instance (loaded from config if None)
        
    Returns:
        tuple[List[str], TokenUsage]: (queries, token_usage)
    """
    from ..models import TokenUsage
    from ..utils.monitoring import UsageTracker
    from ..utils.config import Config
    
    # If no LLM client, use simple query expansion
    if llm_client is None:
        # Simple fallback: return the original query with variations
        queries = [query]
        if max_queries > 1:
            words = query.split()
            if len(words) > 1:
                queries.append(" ".join(words[:len(words)//2]))
                queries.append(" ".join(words[len(words)//2:]))
        return queries[:max_queries], TokenUsage()
    
    try:
        # UPDATED PROMPT: Use error message context to generate better queries
        prompt = f"""Task: Generate {max_queries} Google search queries for the topic: "{query}"

Context from previous attempt: {context if context else "First attempt"}

CRITICAL INSTRUCTION:
If the context mentions "Insufficient sources", you MUST generate DIFFERENT queries than before. 
Try broader terms, synonyms, or break the topic into smaller sub-questions.

Return only {max_queries} lines. No numbers, no bullets, just one query per line."""

        # Use LLM to generate queries
        response = await llm_client.ainvoke(prompt)
        
        # Extract usage
        config = Config.load()
        usage = UsageTracker.extract_usage(response, config.LLM_MODEL)
        
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Parse queries from response (one per line)
        queries = []
        for line in content.strip().split('\n'):
            line = line.strip()
            # Remove numbering if present (e.g., "1. ", "1) ", "- ")
            for prefix in ['1.', '2.', '3.', '4.', '5.', '1)', '2)', '3)', '4)', '5)', '-', '*']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
            if line and len(line) > 3:  # Filter out empty or too short lines
                queries.append(line)
        
        # Fallback if LLM didn't return enough queries
        if len(queries) < max_queries:
            # Add variations of original query
            words = query.split()
            if len(words) > 1:
                queries.append(" ".join(words[:len(words)//2]))
                queries.append(" ".join(words[len(words)//2:]))
            # Ensure we have at least the original query
            if query not in queries:
                queries.insert(0, query)
        
        return queries[:max_queries], usage
    except Exception as e:
        logger.warning(f"Failed to generate search queries with LLM: {e}")
        # Fallback to simple variations
        queries = [query]
        if max_queries > 1:
            words = query.split()
            if len(words) > 1:
                queries.append(" ".join(words[:len(words)//2]))
                queries.append(" ".join(words[len(words)//2:]))
        return queries[:max_queries], TokenUsage()


async def perform_web_search(
    search_query: str,
    max_results: int = 10,
    api_key: Optional[str] = None,
    provider: str = "tavily"
) -> List[dict]:
    """
    Performs async web search using configured search API.
    
    Args:
        search_query: Search query string
        max_results: Maximum results to return
        api_key: API key (loaded from config if None)
        provider: Search provider ("tavily", "serper", or "custom")
        
    Returns:
        List[dict]: List of search results with keys:
            - url: str
            - title: str
            - snippet: str
            - relevance_score: float
            
    Raises:
        SearchAPIException: If search API fails
    """
    config = Config.load()
    api_key = api_key or config.SEARCH_API_KEY
    provider = provider or config.SEARCH_API_PROVIDER
    
    if not api_key:
        logger.warning("No search API key configured. Using mock results for testing.")
        # Return mock results for testing
        return [
            {
                "url": f"https://example.com/result-{i}",
                "title": f"Result {i} for: {search_query}",
                "snippet": f"This is a mock result snippet for query: {search_query}",
                "relevance_score": 0.8 - (i * 0.1)
            }
            for i in range(min(max_results, 5))
        ]
    
    try:
        if provider == "tavily":
            return await _search_tavily(search_query, max_results, api_key)
        elif provider == "serper":
            return await _search_serper(search_query, max_results, api_key)
        else:
            raise SearchAPIException(f"Unknown search provider: {provider}")
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise SearchAPIException(f"Search failed: {str(e)}")


async def _search_tavily(query: str, max_results: int, api_key: str) -> List[dict]:
    """Search using Tavily API"""
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "basic"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise SearchAPIException(f"Tavily API returned status {response.status}")
            
            data = await response.json()
            results = []
            
            for item in data.get("results", []):
                results.append({
                    "url": item.get("url", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("content", ""),
                    "relevance_score": item.get("score", 0.5)
                })
            
            return results


async def _search_serper(query: str, max_results: int, api_key: str) -> List[dict]:
    """Search using Serper API"""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": max_results
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                raise SearchAPIException(f"Serper API returned status {response.status}")
            
            data = await response.json()
            results = []
            
            for item in data.get("organic", []):
                results.append({
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "relevance_score": 0.8  # Serper doesn't provide scores
                })
            
            return results


async def filter_and_rank_sources(
    sources: List[Source],
    query: str,
    min_relevance: float = 0.3
) -> List[Source]:
    """
    Filters and ranks sources by relevance to query.
    
    Args:
        sources: List of candidate sources
        query: Original user query
        min_relevance: Minimum relevance score threshold
        
    Returns:
        List[Source]: Filtered and ranked sources
    """
    # Filter by minimum relevance
    filtered = [s for s in sources if s.relevance_score >= min_relevance]
    
    # Sort by relevance score (descending)
    filtered.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return filtered


async def research_node(state: dict) -> dict:
    """
    LangGraph node function for research phase.
    Performs web search and collects sources.
    
    Args:
        state: Current graph state
        
    Returns:
        dict: Updated state with sources and search results
    """
    from ..models import ResearchStatus
    
    query = state.get("query", "")
    config = Config.load()
    
    logger.info(f"Starting research for query: {query}")
    
    try:
        # Update status
        state["status"] = ResearchStatus.RESEARCHING.value
        state["current_agent"] = "research"
        
        # CAPTURE THE FEEDBACK from previous attempt
        previous_error = state.get("error_message")
        
        # Load LLM client for query generation
        from ..utils.llm_client import create_llm_client
        try:
            llm_client = create_llm_client()
        except Exception as e:
            logger.warning(f"Could not create LLM client: {e}. Using fallback query generation.")
            llm_client = None
        
        # 1. Generate search queries
        try:
            search_queries, usage = await generate_search_queries(
                query,
                context=previous_error,  # Pass error message as context
                max_queries=config.MAX_SEARCH_QUERIES,
                llm_client=llm_client
            )
            state["search_queries"] = search_queries
        except Exception as e:
            msg = f"Failed to generate search queries using {config.LLM_MODEL}: {str(e)}"
            logger.error(msg)
            state["status"] = ResearchStatus.FAILED.value
            state["error_message"] = msg
            return state
        
        # Track usage
        if "usage" not in state or state["usage"] is None:
            from ..models import TokenUsage
            state["usage"] = TokenUsage().model_dump()
            
        current_usage = state["usage"]
        # Update usage (assuming dict for state)
        current_usage["prompt_tokens"] = current_usage.get("prompt_tokens", 0) + usage.prompt_tokens
        current_usage["completion_tokens"] = current_usage.get("completion_tokens", 0) + usage.completion_tokens
        current_usage["total_tokens"] = current_usage.get("total_tokens", 0) + usage.total_tokens
        current_usage["estimated_cost_usd"] = current_usage.get("estimated_cost_usd", 0.0) + usage.estimated_cost_usd
        state["usage"] = current_usage
        
        # Perform searches concurrently
        search_tasks = [
            perform_web_search(
                sq,
                max_results=config.MAX_SOURCES_PER_QUERY // len(search_queries),
                provider=config.SEARCH_API_PROVIDER
            )
            for sq in search_queries
        ]
        
        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        sources = []
        raw_results = []
        
        for i, results in enumerate(all_results):
            if isinstance(results, Exception):
                query_text = search_queries[i] if i < len(search_queries) else "unknown"
                logger.warning(f"Search failed for query '{query_text}' using {config.SEARCH_API_PROVIDER}: {results}")
                continue
            
            raw_results.extend(results)
            
            for result in results:
                source = Source(
                    url=result.get("url", ""),
                    title=result.get("title", ""),
                    snippet=result.get("snippet", ""),
                    relevance_score=result.get("relevance_score", 0.5)
                )
                sources.append(source)
        
        # Filter and rank sources
        sources = await filter_and_rank_sources(
            sources,
            query,
            min_relevance=config.MIN_RELEVANCE_SCORE
        )
        
        # Limit to max sources
        sources = sources[:config.MAX_SOURCES_PER_QUERY]
        
        # Convert sources to dict for state
        state["sources"] = [s.model_dump() for s in sources]
        state["raw_search_results"] = raw_results
        
        logger.info(f"Research completed. Found {len(sources)} sources.")
        
    except Exception as e:
        logger.error(f"Research failed: {e}")
        state["status"] = ResearchStatus.FAILED.value
        state["error_message"] = str(e)
    
    return state
