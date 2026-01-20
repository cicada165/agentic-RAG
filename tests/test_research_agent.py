"""
Tests for Research Agent
"""
import pytest
from src.agents.research_agent import (
    generate_search_queries,
    filter_and_rank_sources,
    perform_web_search
)
from src.models import Source


@pytest.mark.asyncio
async def test_generate_search_queries():
    """Test search query generation"""
    queries = await generate_search_queries("test query", max_queries=3)
    
    assert isinstance(queries, list)
    assert len(queries) > 0
    assert "test query" in queries[0] or queries[0] == "test query"


@pytest.mark.asyncio
async def test_perform_web_search_no_key(monkeypatch):
    """Test web search without API key (should return mock results)"""
    # Set a dummy API key to pass config validation
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    results = await perform_web_search("test query", max_results=5, api_key=None)
    
    assert isinstance(results, list)
    assert len(results) > 0
    assert "url" in results[0]
    assert "title" in results[0]
    assert "snippet" in results[0]


@pytest.mark.asyncio
async def test_filter_and_rank_sources():
    """Test source filtering and ranking"""
    sources = [
        Source(
            url=f"https://example.com/{i}",
            title=f"Source {i}",
            snippet=f"Snippet {i}",
            relevance_score=0.9 - (i * 0.1)
        )
        for i in range(5)
    ]
    
    filtered = await filter_and_rank_sources(sources, "test query", min_relevance=0.5)
    
    assert len(filtered) <= len(sources)
    # Check that sources are sorted by relevance (descending)
    for i in range(len(filtered) - 1):
        assert filtered[i].relevance_score >= filtered[i + 1].relevance_score


@pytest.mark.asyncio
async def test_research_node(monkeypatch):
    """Test research_node function"""
    from src.agents.research_agent import research_node
    
    # Set a dummy API key to pass config validation
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    
    state = {
        "query": "test query",
        "query_id": "test-123",
        "status": "pending",
        "sources": [],
        "search_queries": [],
        "raw_search_results": []
    }
    
    result_state = await research_node(state)
    
    assert "sources" in result_state
    assert "search_queries" in result_state
    assert result_state["status"] in ["researching", "failed", "completed"]
