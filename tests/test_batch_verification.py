
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from src.agents.reviewer_agent import verify_sources_batch
from src.models import Source

@pytest.mark.asyncio
async def test_verify_sources_batch_success():
    # Setup mock sources
    sources = [
        Source(
            url="http://example.com/1",
            title="Source 1",
            snippet="This is a valid source with specific data about the topic.",
            relevance_score=0.9,
            accessed_at=datetime.now()
        ),
        Source(
            url="http://example.com/2",
            title="Source 2",
            snippet="Generic SEO spam content that doesn't say anything useful.",
            relevance_score=0.8,
            accessed_at=datetime.now()
        )
    ]
    
    # Setup mock LLM
    mock_llm = MagicMock()
    mock_response = MagicMock()
    # Mock JSON response from LLM
    mock_response.content = '[{"id": 1, "valid": true}, {"id": 2, "valid": false}]'
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    # Execute batch verification
    results = await verify_sources_batch(sources, "test query", mock_llm)
    
    # Assertions
    assert len(results) == 2
    assert results[0][0] is True  # Source 1 is valid
    assert results[1][0] is False # Source 2 is invalid
    
    # Verify LLM was called
    mock_llm.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_verify_sources_batch_fallback():
    # Setup mock sources
    sources = [
        Source(
            url="http://example.com/1",
            title="Source 1",
            snippet="Valid snippet long enough to pass filter.",
            relevance_score=0.5,
            accessed_at=datetime.now()
        )
    ]
    
    # Execute without LLM client (should fallback to relevance score)
    results = await verify_sources_batch(sources, "test query", None)
    
    assert len(results) == 1
    assert results[0][0] is True # 0.5 > 0.4 threshold

@pytest.mark.asyncio
async def test_verify_sources_batch_garbage_filter():
    # Setup mock sources with short snippet
    sources = [
        Source(
            url="http://example.com/1",
            title="Source 1",
            snippet="Too short",
            relevance_score=0.9,
            accessed_at=datetime.now()
        )
    ]
    
    mock_llm = MagicMock()
    
    # Execute
    results = await verify_sources_batch(sources, "test query", mock_llm)
    
    assert len(results) == 1
    assert results[0][0] is False # Rejected by hard filter
    # LLM should NOT be called for garbage
    mock_llm.ainvoke.assert_not_called()
