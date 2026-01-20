"""
Tests for data models
"""
import pytest
from datetime import datetime
from src.models import (
    ResearchStatus,
    Source,
    ResearchState,
    AgentResponse,
    StreamEvent
)


def test_research_status_enum():
    """Test ResearchStatus enum values"""
    assert ResearchStatus.PENDING == "pending"
    assert ResearchStatus.RESEARCHING == "researching"
    assert ResearchStatus.COMPLETED == "completed"


def test_source_creation():
    """Test Source model creation"""
    source = Source(
        url="https://example.com",
        title="Test Source",
        snippet="This is a test snippet",
        relevance_score=0.8
    )
    
    assert source.url == "https://example.com"
    assert source.title == "Test Source"
    assert source.relevance_score == 0.8
    assert source.verified is False
    assert isinstance(source.accessed_at, datetime)


def test_source_relevance_validation():
    """Test Source relevance score validation"""
    # Valid score
    source = Source(
        url="https://example.com",
        title="Test",
        snippet="Test",
        relevance_score=0.5
    )
    assert source.relevance_score == 0.5
    
    # Invalid score (too high)
    with pytest.raises(Exception):
        Source(
            url="https://example.com",
            title="Test",
            snippet="Test",
            relevance_score=1.5
        )
    
    # Invalid score (too low)
    with pytest.raises(Exception):
        Source(
            url="https://example.com",
            title="Test",
            snippet="Test",
            relevance_score=-0.1
        )


def test_research_state_creation():
    """Test ResearchState model creation"""
    state = ResearchState(
        query="Test query",
        query_id="test-123"
    )
    
    assert state.query == "Test query"
    assert state.query_id == "test-123"
    assert state.status == ResearchStatus.PENDING
    assert state.sources == []
    assert state.verified_sources == []
    assert state.confidence_score == 0.0


def test_research_state_defaults():
    """Test ResearchState default values"""
    state = ResearchState(
        query="Test",
        query_id="test"
    )
    
    assert state.max_iterations == 5
    assert state.iteration_count == 0
    assert state.sources == []
    assert state.search_queries == []
    assert state.final_report is None


def test_stream_event_creation():
    """Test StreamEvent model creation"""
    event = StreamEvent(
        event_type="status",
        query_id="test-123",
        agent="research",
        data={"status": "researching"}
    )
    
    assert event.event_type == "status"
    assert event.query_id == "test-123"
    assert event.agent == "research"
    assert event.data["status"] == "researching"
    assert isinstance(event.timestamp, datetime)


def test_agent_response_creation():
    """Test AgentResponse model creation"""
    response = AgentResponse(
        agent_name="research",
        status="success",
        message="Research completed"
    )
    
    assert response.agent_name == "research"
    assert response.status == "success"
    assert response.message == "Research completed"
    assert response.data == {}
    assert isinstance(response.timestamp, datetime)
