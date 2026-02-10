"""
Data models for Deep Research Assistant
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal, Any
from datetime import datetime
from enum import Enum


class ResearchStatus(str, Enum):
    """Research workflow status"""
    PENDING = "pending"
    RESEARCHING = "researching"
    REVIEWING = "reviewing"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NEEDS_REVISION = "needs_revision"  # Triggers loop back to research


class Source(BaseModel):
    """Individual source from research"""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    snippet: str = Field(..., description="Relevant snippet from source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score 0-1")
    accessed_at: datetime = Field(default_factory=datetime.now)
    verified: bool = Field(default=False, description="Whether source was fact-checked")

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class TokenUsage(BaseModel):
    """Tracking for LLM token usage and costs"""
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    estimated_cost_usd: float = Field(default=0.0)

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd
        )


class ResearchState(BaseModel):
    """Main state model for research workflow"""
    # User Input
    query: str = Field(..., description="Original user query")
    query_id: str = Field(..., description="Unique identifier for this research session")
    
    # Workflow State
    status: ResearchStatus = Field(default=ResearchStatus.PENDING)
    current_agent: Optional[str] = Field(default=None, description="Currently active agent")
    iteration_count: int = Field(default=0, ge=0, description="Number of research iterations")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum research iterations")
    
    # Usage Tracking
    usage: TokenUsage = Field(default_factory=TokenUsage, description="Cumulative token usage")
    
    # Research Results
    sources: List[Source] = Field(default_factory=list, description="Collected sources")
    search_queries: List[str] = Field(default_factory=list, description="Generated search queries")
    raw_search_results: List[dict] = Field(default_factory=list, description="Raw API responses")
    
    # Review Results
    verified_sources: List[Source] = Field(default_factory=list, description="Fact-checked sources")
    conflicting_claims: List[str] = Field(default_factory=list, description="Conflicting information found")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")
    
    # Report Generation
    draft_report: str = Field(default="", description="Draft markdown report")
    final_report: Optional[str] = Field(default=None, description="Final markdown report")
    citations: List[str] = Field(default_factory=list, description="Citation URLs for report")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_seconds: Optional[float] = Field(default=None, description="Total execution time")
    
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class AgentResponse(BaseModel):
    """Base response from any agent"""
    agent_name: str
    status: Literal["success", "partial", "failed"]
    message: str
    data: dict = Field(default_factory=dict)
    usage: TokenUsage = Field(default_factory=TokenUsage)
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )


class ResearchAgentResponse(AgentResponse):
    """Response from Research Agent"""
    sources_found: int
    search_queries_used: List[str]
    raw_results: List[dict]


class ReviewerAgentResponse(AgentResponse):
    """Response from Reviewer Agent"""
    sources_verified: int
    sources_rejected: int
    confidence_score: float
    conflicts_detected: List[str]


class WriterAgentResponse(AgentResponse):
    """Response from Writer Agent"""
    report_length: int
    citation_count: int
    sections: List[str]


class StreamEvent(BaseModel):
    """Event for streaming to UI"""
    event_type: Literal["status", "source", "progress", "report_chunk", "error", "complete"]
    query_id: str
    agent: Optional[str] = None
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )
