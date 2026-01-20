# SPECS.md - Deep Research Assistant Technical Specifications

## 1. System Architecture Overview

### 1.1 High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat UI      │  │ Status Panel │  │ Report View  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            │ Async Event Stream
                            │
┌───────────────────────────┼──────────────────────────────────┐
│                    LangGraph Backend                         │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │         ResearchState (Pydantic Model)           │        │
│  └────────────────────────┼────────────────────────┘        │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │              Agent Orchestration                 │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │        │
│  │  │ Research │→ │ Reviewer │→ │  Writer  │     │        │
│  │  │  Agent   │  │  Agent   │  │  Agent   │     │        │
│  │  └──────────┘  └──────────┘  └──────────┘     │        │
│  └─────────────────────────────────────────────────┘        │
│                           │                                  │
│  ┌────────────────────────┼────────────────────────┐        │
│  │         External Services                         │        │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │        │
│  │  │  Search  │  │   LLM    │  │  Cache   │      │        │
│  │  │   API    │  │   API    │  │  Store   │      │        │
│  │  └──────────┘  └──────────┘  └──────────┘      │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack
- **Frontend**: Streamlit (Python web framework)
- **Backend Orchestration**: LangGraph (workflow management)
- **LLM**: DeepSeek API (configurable via environment)
- **Search**: Web search API (Tavily, Serper, or custom)
- **State Management**: Pydantic models
- **Async Framework**: asyncio, aiohttp
- **Caching**: In-memory (Redis optional for production)

---

## 2. Data Models

### 2.1 ResearchState (Core State Model)
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
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
    NEEDS_REVISION = "needs_revision"  # Quality-based revision loop trigger

class Source(BaseModel):
    """Individual source from research"""
    url: str = Field(..., description="Source URL")
    title: str = Field(..., description="Source title")
    snippet: str = Field(..., description="Relevant snippet from source")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score 0-1")
    accessed_at: datetime = Field(default_factory=datetime.now)
    verified: bool = Field(default=False, description="Whether source was fact-checked")

class ResearchState(BaseModel):
    """
    Main state model for research workflow.
    
    This model is decoupled from UI rendering and serves as the single source of truth
    for research progress. It supports the "Recursive Research" loop by tracking
    iterations and refinement history.
    """
    # User Input
    query: str = Field(..., description="Original user query", max_length=1000)
    query_id: str = Field(..., description="Unique identifier for this research session")
    
    # Workflow State
    status: ResearchStatus = Field(default=ResearchStatus.PENDING)
    current_agent: Optional[str] = Field(default=None, description="Currently active agent")
    
    # Recursive Research Loop Fields
    iteration_count: int = Field(default=0, ge=0, description="Number of research iterations completed")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Maximum research iterations allowed")
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Confidence threshold for stopping research")
    iteration_history: List[dict] = Field(
        default_factory=list,
        description="History of each iteration with queries, sources found, and confidence scores"
    )
    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Identified gaps in current research that need refinement"
    )
    refinement_strategy: Optional[Literal["broaden", "deepen", "verify", "complete"]] = Field(
        default=None,
        description="Strategy for next iteration of research"
    )
    
    # Research Results (Accumulated across iterations)
    sources: List[Source] = Field(default_factory=list, description="All collected sources across iterations")
    search_queries: List[str] = Field(default_factory=list, description="All generated search queries across iterations")
    raw_search_results: List[dict] = Field(default_factory=list, description="Raw API responses from all searches")
    
    # Review Results
    verified_sources: List[Source] = Field(default_factory=list, description="All fact-checked sources")
    conflicting_claims: List[str] = Field(default_factory=list, description="Conflicting information found")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Current overall confidence score")
    confidence_history: List[float] = Field(
        default_factory=list,
        description="Confidence scores from each iteration for trend analysis"
    )
    
    # Report Generation
    draft_report: str = Field(default="", description="Draft markdown report (updated incrementally)")
    final_report: Optional[str] = Field(default=None, description="Final markdown report")
    citations: List[str] = Field(default_factory=list, description="Citation URLs for report in order of appearance")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    execution_time_seconds: Optional[float] = Field(default=None, description="Total execution time")
    
    # State Isolation (for concurrent queries)
    _lock: Optional[Any] = Field(default=None, exclude=True, description="Async lock for state updates")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Ensure model is serializable for session state
        arbitrary_types_allowed = True
```

### 2.2 Agent Response Models
```python
class AgentResponse(BaseModel):
    """Base response from any agent"""
    agent_name: str
    status: Literal["success", "partial", "failed"]
    message: str
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)

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
```

### 2.3 Stream Event Model
```python
class StreamEvent(BaseModel):
    """Event for streaming to UI"""
    event_type: Literal["status", "source", "progress", "report_chunk", "error", "complete"]
    query_id: str
    agent: Optional[str] = None
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
```

---

## 3. API Signatures

### 3.1 Streamlit Frontend API

#### 3.1.1 Main Application Entry Point
```python
# File: src/main.py

def main() -> None:
    """
    Main Streamlit application entry point.
    Initializes session state and renders UI components.
    """
    pass
```

#### 3.1.2 UI Component Functions
```python
# File: src/components/chat_interface.py

def render_chat_input() -> Optional[str]:
    """
    Renders chat input widget.
    
    Returns:
        Optional[str]: User query if submitted, None otherwise
    """
    pass

def render_message_history(messages: List[dict]) -> None:
    """
    Renders chat message history.
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys
    """
    pass

def render_status_panel(state: ResearchState) -> None:
    """
    Renders research status panel with progress indicators.
    
    Args:
        state: Current ResearchState instance
    """
    pass

def render_report_viewer(report: str, citations: List[str]) -> None:
    """
    Renders final report with markdown formatting and citations.
    
    Args:
        report: Markdown-formatted report string
        citations: List of citation URLs
    """
    pass

def render_error_message(error: str) -> None:
    """
    Renders user-friendly error message.
    
    Args:
        error: Error message string
    """
    pass
```

#### 3.1.3 State Management Functions
```python
# File: src/utils/state_manager.py

def initialize_session_state() -> None:
    """
    Initializes Streamlit session state with default values.
    Creates: research_states, current_query_id, active_research
    """
    pass

def get_current_state(query_id: str) -> Optional[ResearchState]:
    """
    Retrieves ResearchState for given query_id from session state.
    
    Args:
        query_id: Unique query identifier
        
    Returns:
        Optional[ResearchState]: State if found, None otherwise
    """
    pass

def update_state(query_id: str, state: ResearchState) -> None:
    """
    Updates ResearchState in session state and triggers UI rerun.
    
    Args:
        query_id: Unique query identifier
        state: Updated ResearchState instance
    """
    pass

def clear_completed_research() -> None:
    """
    Clears completed research states from session to free memory.
    """
    pass
```

### 3.2 LangGraph Backend API

#### 3.2.1 Workflow Orchestration
```python
# File: src/agents/orchestrator.py

from langgraph.graph import StateGraph
from typing import TypedDict

class GraphState(TypedDict):
    """LangGraph state compatible with ResearchState"""
    query: str
    query_id: str
    status: str
    sources: List[dict]
    verified_sources: List[dict]
    draft_report: str
    final_report: Optional[str]
    citations: List[str]
    error_message: Optional[str]

def create_research_graph() -> StateGraph:
    """
    Creates LangGraph workflow for research pipeline with quality-based revision loop.
    
    Returns:
        StateGraph: Configured graph with nodes and edges:
            - Nodes: research_node, review_node, write_node, error_handler_node
            - Edges: 
                * research → review (conditional: continue or error)
                * review → write OR research (conditional: continue, needs_revision, or error)
                * write → end
            - Conditional edges:
                * review → research: When status is NEEDS_REVISION (quality threshold not met)
                * review → write: When quality threshold met or max_iterations reached
                * All nodes → error_handler: On failure status
    
    Revision Loop:
        The graph supports automatic revision by routing review → research
        when NEEDS_REVISION status is detected, up to max_iterations limit.
    """
    pass

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
    pass

async def decision_node(state: GraphState) -> Literal["continue", "stop"]:
    """
    LangGraph decision node for recursive research loop.
    Determines whether to continue research or proceed to writing.
    
    Args:
        state: Current graph state with confidence and iteration info
        
    Returns:
        Literal["continue", "stop"]: Decision on whether to continue research
    """
    pass

async def refine_node(state: GraphState) -> GraphState:
    """
    LangGraph node for refining research queries before next iteration.
    Analyzes gaps and generates refined search queries.
    
    Args:
        state: Current graph state with iteration history
        
    Returns:
        GraphState: Updated state with refined queries and strategy
    """
    pass

#### 3.2.2 Research Agent
```python
# File: src/agents/research_agent.py

async def research_node(state: GraphState) -> GraphState:
    """
    LangGraph node function for research phase.
    Performs web search and collects sources.
    
    **Agentic Intelligence**: Captures error_message from state and passes it as
    context to generate_search_queries, enabling the agent to learn from feedback
    and generate different queries on revision attempts.
    
    Args:
        state: Current graph state (may contain error_message from previous attempt)
        
    Returns:
        GraphState: Updated state with sources and search results
        
    Process:
        1. Captures error_message from state (feedback from reviewer)
        2. Loads LLM client for intelligent query generation
        3. Passes error_message as context to generate_search_queries
        4. Performs concurrent web searches
        5. Filters and ranks sources
    """
    pass

async def generate_search_queries(
    query: str,
    context: Optional[str] = None,  # Changed to str to accept error messages
    max_queries: int = 5,
    llm_client: Optional[Any] = None
) -> List[str]:
    """
    Generates optimized search queries from user query using LLM intelligence.
    
    **Agentic Intelligence**: Uses error message context to generate DIFFERENT queries
    on revision attempts, preventing blind retries.
    
    Args:
        query: Original user query
        context: Optional error message/feedback from previous attempt (str)
                 Used to instruct LLM to generate different queries on revision
        max_queries: Maximum number of queries to generate
        llm_client: LLM client instance (required for intelligent generation)
        
    Returns:
        List[str]: List of search query strings
        
    Prompt Engineering:
        - If context mentions "Insufficient sources", instructs LLM to generate
          DIFFERENT queries (broader terms, synonyms, sub-questions)
        - Prevents blind retries by learning from feedback
        
    Fallback:
        - If LLM unavailable, uses simple query variations
    """
    pass

async def perform_web_search(
    search_query: str,
    max_results: int = 10,
    api_key: Optional[str] = None
) -> List[dict]:
    """
    Performs async web search using configured search API.
    
    Args:
        search_query: Search query string
        max_results: Maximum results to return
        api_key: API key (loaded from config if None)
        
    Returns:
        List[dict]: List of search results with keys:
            - url: str
            - title: str
            - snippet: str
            - relevance_score: float
            
    Raises:
        SearchAPIException: If search API fails
    """
    pass

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
    pass
```

#### 3.2.3 Reviewer Agent
```python
# File: src/agents/reviewer_agent.py

async def review_node(state: GraphState) -> GraphState:
    """
    LangGraph node function for review phase.
    Fact-checks sources and identifies conflicts using LLM intelligence.
    
    **Agentic Intelligence**: Uses LLM to verify sources intelligently, distinguishing
    between specific facts/data and generic SEO spam.
    
    **Quality-Based Revision**: If insufficient verified sources are found,
    returns state with NEEDS_REVISION status to trigger revision loop.
    
    Args:
        state: Current graph state with sources
        
    Returns:
        GraphState: Updated state with verified sources and confidence.
                   If quality threshold not met, status set to NEEDS_REVISION
                   and sources/queries cleared for revision loop.
    
    Process:
        1. Loads LLM client for intelligent verification
        2. Verifies each source using LLM (via verify_source)
        3. Detects conflicts across sources
        4. Calculates overall confidence score
        5. Checks quality threshold (minimum 2 verified sources)
        6. Triggers revision if threshold not met (unless max_iterations reached)
    
    Quality Threshold:
        - Minimum 2 verified sources required (configurable)
        - If threshold not met and max_iterations not reached, triggers revision
        - If max_iterations reached, proceeds to write with available sources
    """
    pass

async def verify_source(
    source: Source,
    query: str,
    llm_client: Optional[Any] = None
) -> tuple[bool, float]:
    """
    Verifies a single source for factual accuracy and relevance using LLM intelligence.
    
    **Agentic Intelligence**: Uses LLM to distinguish between specific facts/data
    and generic SEO spam, rather than blindly trusting search engine relevance scores.
    
    Args:
        source: Source to verify
        query: Original research query
        llm_client: LLM client instance (required for intelligent verification)
        
    Returns:
        tuple[bool, float]: (is_verified, confidence_score)
            - is_verified: Whether source passes verification
            - confidence_score: Confidence level 0.0-1.0
            
    Verification Process:
        1. **Hard Filter**: Snippet must be ≥50 characters (increased from 20)
        2. **LLM Verification**: Asks LLM if snippet contains specific facts/data
           vs generic SEO spam
        3. **Fallback**: Uses relevance_score > 0.4 if LLM unavailable/fails
        
    LLM Prompt:
        "Verify if this text answers the query: {query}
         Text: {snippet}
         Return YES only if the text contains specific facts/data. 
         Return NO if it is generic SEO spam."
    """
    pass

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
    pass

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
    pass
```

#### 3.2.4 Writer Agent
```python
# File: src/agents/writer_agent.py

async def write_node(state: GraphState) -> GraphState:
    """
    LangGraph node function for writing phase.
    Generates final markdown report with citations.
    
    Args:
        state: Current graph state with verified sources
        
    Returns:
        GraphState: Updated state with final report
    """
    pass

async def generate_report(
    query: str,
    verified_sources: List[Source],
    conflicts: Optional[List[str]] = None,
    llm_client: Optional[Any] = None
) -> tuple[str, List[str]]:
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
    pass

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
    pass
```

### 3.3 Configuration and Utilities

#### 3.3.1 Configuration Management
```python
# File: src/utils/config.py

class Config:
    """Application configuration loaded from environment"""
    
    # API Keys (loaded from st.secrets or .env)
    # CRITICAL: No hardcoded defaults - must raise ConfigError if missing
    DEEPSEEK_API_KEY: str  # Required - raises ConfigError if missing
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    SEARCH_API_KEY: Optional[str] = None  # Optional - some providers don't need it
    SEARCH_API_PROVIDER: Literal["tavily", "serper", "custom"] = "tavily"
    TAVILY_API_KEY: Optional[str] = None  # Required if provider is "tavily"
    
    # Workflow Settings
    MAX_RESEARCH_ITERATIONS: int = 5
    MAX_SOURCES_PER_QUERY: int = 20
    MIN_RELEVANCE_SCORE: float = 0.3
    MAX_CONCURRENT_SEARCHES: int = 5
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT_SECONDS: int = 60
    
    # UI Settings
    STREAM_UPDATE_INTERVAL_MS: int = 500
    MAX_HISTORY_ITEMS: int = 10
    
    @classmethod
    def load(cls) -> "Config":
        """
        Loads configuration from environment variables.
        Prioritizes Streamlit secrets, falls back to .env file.
        
        Loading Priority:
        1. Streamlit secrets (st.secrets) - for cloud deployment
        2. Environment variables (os.getenv) - for local development
        3. .env file (python-dotenv) - fallback for local
        
        Returns:
            Config: Configured instance
            
        Raises:
            ConfigError: If required API keys are missing (DEEPSEEK_API_KEY)
            ConfigError: If SEARCH_API_PROVIDER is set but corresponding key is missing
            
        Security Rules:
        - NEVER use placeholder/default values for API keys
        - NEVER log API keys in error messages
        - ALWAYS raise ConfigError with user-friendly message if keys are missing
        """
        # Implementation must:
        # 1. Try st.secrets first (if available)
        # 2. Fall back to os.getenv()
        # 3. Fall back to python-dotenv .env file
        # 4. Raise ConfigError with message like:
        #    "DEEPSEEK_API_KEY not found. Please set it in Streamlit secrets or .env file"
        pass
```

#### 3.3.2 Error Handling
```python
# File: src/utils/exceptions.py

class ResearchException(Exception):
    """Base exception for research workflow"""
    pass

class SearchAPIException(ResearchException):
    """Exception for search API failures"""
    pass

class LLMException(ResearchException):
    """Exception for LLM API failures"""
    pass

class ConfigError(ResearchException):
    """Exception for configuration errors"""
    pass

class ValidationError(ResearchException):
    """Exception for data validation errors"""
    pass
```

#### 3.3.3 Logging
```python
# File: src/utils/logger.py

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Sets up structured logger for application.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    pass
```

---

## 4. Database Schemas (Optional - For Persistent Storage)

### 4.1 Research Session Table
```sql
CREATE TABLE research_sessions (
    query_id VARCHAR(255) PRIMARY KEY,
    query TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    execution_time_seconds FLOAT NULL,
    error_message TEXT NULL,
    final_report TEXT NULL,
    confidence_score FLOAT,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
```

### 4.2 Sources Table
```sql
CREATE TABLE sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    title VARCHAR(500),
    snippet TEXT,
    relevance_score FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id) ON DELETE CASCADE,
    INDEX idx_query_id (query_id),
    INDEX idx_verified (verified)
);
```

### 4.3 Citations Table
```sql
CREATE TABLE citations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    source_id INT NOT NULL,
    citation_order INT NOT NULL,
    FOREIGN KEY (query_id) REFERENCES research_sessions(query_id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE,
    UNIQUE KEY unique_citation (query_id, citation_order)
);
```

---

## 5. Async Data Flow Architecture

### 5.1 Request Flow
```
User Input (Streamlit)
    ↓
[Async] Initialize ResearchState
    ↓
[Async] Create LangGraph workflow
    ↓
[Async] Research Agent → Search API (parallel requests)
    ↓
[Stream] Emit source events to UI
    ↓
[Async] Reviewer Agent → LLM API (batched requests)
    ↓
[Stream] Emit verification events to UI
    ↓
[Async] Writer Agent → LLM API
    ↓
[Stream] Emit report chunks to UI
    ↓
[Sync] Update session state
    ↓
UI Renders Final Report
```

### 5.2 Streaming Mechanism
```python
# File: src/utils/streaming.py

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
    def callback(event: StreamEvent) -> None:
        # Update session state
        # Trigger st.rerun() if needed
        pass
    return callback
```

### 5.3 Async Pattern Implementation

#### 5.3.1 Preventing UI Freezing
The Streamlit UI must remain responsive during long-running research operations. The following patterns ensure non-blocking behavior:

1. **All External API Calls Are Async**
   - Search API calls: `async def perform_web_search()` - never blocks UI thread
   - LLM API calls: `async def generate_report()` - uses async HTTP clients
   - All I/O operations: File reads, database queries use async variants

2. **Concurrent Operations with asyncio.gather()**
   ```python
   # Example: Parallel search queries
   search_tasks = [
       perform_web_search(query) 
       for query in search_queries
   ]
   results = await asyncio.gather(*search_tasks, return_exceptions=True)
   ```

3. **Streamlit Async Integration Pattern**
   ```python
   # Pattern: Use asyncio.create_task() for background work
   async def run_research_async(query: str):
       # Long-running async operation
       result = await research_workflow(query)
       return result
   
   # In Streamlit handler:
   if st.button("Research"):
       task = asyncio.create_task(run_research_async(query))
       # UI remains responsive, task runs in background
   ```

4. **Streaming Updates Without Blocking**
   - Use `st.rerun()` only when state actually changes
   - Batch UI updates to prevent excessive reruns
   - Use `st.empty()` containers for dynamic content updates

5. **Async Context Managers for Resource Cleanup**
   ```python
   async with aiohttp.ClientSession() as session:
       # All HTTP requests use async session
       # Automatically cleaned up on exit
   ```

#### 5.3.2 State Isolation for Concurrent Queries
Each research session must be isolated to prevent race conditions:

- **Session State Structure**: `st.session_state.research_states[query_id] = ResearchState`
- **Query ID Generation**: UUID4 for each new query ensures uniqueness
- **State Locking**: Use asyncio.Lock per query_id during state updates
- **Concurrent Query Handling**: Multiple queries can run simultaneously without interference

---

## 6. Scalability Considerations

### 6.1 Horizontal Scaling
- **Stateless agents**: All agents are stateless, allowing multiple instances
- **Session isolation**: Each research session is independent
- **Async I/O**: Non-blocking operations prevent resource exhaustion
- **Connection pooling**: Reuse HTTP connections for API calls

### 6.2 Caching Strategy
- **Search results**: Cache by query hash (TTL: 1 hour)
- **LLM responses**: Cache by (query + sources) hash (TTL: 24 hours)
- **Source verification**: Cache by URL hash (TTL: 7 days)
- **Implementation**: In-memory dict for MVP, Redis for production

### 6.3 Rate Limiting
- **Search API**: Max 10 concurrent requests per user session
- **LLM API**: Max 5 concurrent requests per user session
- **Retry logic**: Exponential backoff with max 3 retries
- **Circuit breaker**: Temporarily disable failing APIs after threshold

### 6.4 Resource Management
- **Memory**: Clear completed research states after 1 hour
- **API quotas**: Track usage per API key, warn at 80% threshold
- **Timeout handling**: All async operations have configurable timeouts
- **Graceful degradation**: Fallback to cached results if APIs fail

### 6.5 Performance Targets
- **Initial response**: < 2 seconds (first source appears)
- **Research phase**: < 30 seconds for 10 sources
- **Review phase**: < 20 seconds for 10 sources
- **Writing phase**: < 15 seconds for report generation
- **Total workflow**: < 90 seconds end-to-end

---

## 7. Security and Privacy

### 7.1 API Key Management
- **Never commit keys**: All keys in `.env` or Streamlit secrets
- **Key rotation**: Support for multiple API keys with fallback
- **Key validation**: Verify keys on startup, fail fast if invalid

### 7.2 Data Privacy
- **No persistent storage**: By default, no user data stored (optional DB)
- **Session isolation**: Each session is independent
- **Source URLs**: Only store public URLs, no authentication required

### 7.3 Input Validation
- **Query sanitization**: Strip malicious characters, limit length (max 1000 chars)
- **URL validation**: Verify source URLs before accessing
- **Rate limiting**: Prevent abuse with per-session limits

---

## 8. Error Handling Patterns

### 8.1 Error Classification
- **Transient errors**: Retry with exponential backoff (network issues)
- **Permanent errors**: Fail fast with user-friendly message (invalid API key)
- **Partial failures**: Continue with available data, log warnings

### 8.2 Error Recovery
- **Search API failure**: Use cached results if available
- **LLM API failure**: Retry up to 3 times, then use simpler fallback
- **Workflow failure**: Save partial state, allow user to resume

### 8.3 User-Facing Error Messages

All error messages must be user-friendly and actionable. Error message templates:

#### 8.3.1 Error Message Templates
```python
# Generic/Unknown Errors
GENERIC_ERROR = "An error occurred while processing your request. Please try again."

# Search API Errors
SEARCH_API_UNAVAILABLE = "Search service is temporarily unavailable. Retrying in {retry_delay}s..."
SEARCH_API_FAILED = "Unable to search the web. Please check your internet connection and try again."
SEARCH_API_QUOTA_EXCEEDED = "Search API quota exceeded. Please try again later or contact support."

# LLM API Errors
LLM_API_UNAVAILABLE = "AI service is temporarily unavailable. Retrying..."
LLM_API_FAILED = "Unable to generate report. Please try again."
LLM_API_TIMEOUT = "AI service took too long to respond. Please try a simpler query."

# Validation Errors
QUERY_TOO_LONG = "Query is too long. Please limit to 1000 characters."
QUERY_EMPTY = "Please enter a research question."
QUERY_INVALID = "Invalid query format. Please use natural language questions."

# Configuration Errors
MISSING_API_KEY = "API key not configured. Please set {key_name} in your environment variables or Streamlit secrets."
INVALID_API_KEY = "API key is invalid. Please check your configuration."

# Workflow Errors
WORKFLOW_FAILED = "Research workflow failed. Error: {error_message}"
PARTIAL_RESULTS = "Some sources could not be verified, but partial results are available."
NO_SOURCES_FOUND = "No relevant sources found for your query. Try rephrasing your question."

# Timeout Errors
REQUEST_TIMEOUT = "Request timed out after {timeout}s. Please try a simpler query or try again later."
```

#### 8.3.2 Error Message Implementation Pattern
```python
def format_user_error(
    error_type: str,
    error_details: Optional[dict] = None
) -> str:
    """
    Formats error for user display.
    
    Args:
        error_type: Error type identifier
        error_details: Optional dict with error context
        
    Returns:
        str: User-friendly error message
    """
    templates = {
        "search_api_unavailable": SEARCH_API_UNAVAILABLE,
        "llm_api_timeout": LLM_API_TIMEOUT,
        # ... etc
    }
    template = templates.get(error_type, GENERIC_ERROR)
    return template.format(**(error_details or {}))
```

---

## 9. Testing Strategy (Architecture Level)

### 9.1 Unit Test Targets
- **State models**: Pydantic validation, serialization
- **Agent functions**: Mock external APIs, test logic
- **Utility functions**: Pure functions, edge cases

### 9.2 Integration Test Targets
- **Workflow orchestration**: End-to-end with mocked APIs
- **Streaming mechanism**: Event generation and consumption
- **State persistence**: Session state updates

### 9.3 Mock Requirements
- **Search API**: Mock responses with realistic data
- **LLM API**: Mock structured responses matching schemas
- **Streamlit**: Mock session state and UI components

---

## 10. Deployment Considerations

### 10.1 Environment Variables
Required variables (documented in `.env.example`):
```
DEEPSEEK_API_KEY=your_key_here
SEARCH_API_KEY=your_key_here
SEARCH_API_PROVIDER=tavily
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
```

### 10.2 Streamlit Cloud Configuration
- **Secrets management**: Use `st.secrets` for API keys
- **Resource limits**: Configure memory and CPU limits
- **Public/private**: Configure access control

### 10.3 Local Development
- **Hot reload**: Streamlit auto-reloads on file changes
- **Debug mode**: Enable verbose logging in development
- **Test mode**: Use mock APIs for offline development

---

## 11. Future Enhancements (Out of Scope for MVP)

### 11.1 Advanced Features
- **Multi-language support**: Research in multiple languages
- **Custom knowledge bases**: Integrate private document stores
- **Collaborative research**: Share research sessions
- **Export formats**: PDF, DOCX, HTML export options

### 11.2 Performance Optimizations
- **Vector search**: Semantic search over source content
- **Incremental updates**: Stream report as it's generated
- **Background processing**: Queue long-running research tasks

### 11.3 Analytics
- **Usage tracking**: Research query patterns
- **Quality metrics**: Source verification success rates
- **Performance monitoring**: API latency, error rates

---

## 12. Recursive Research Loop Architecture

### 12.1 Overview
The "Recursive Research" loop enables iterative refinement of research results. Users can ask broad questions, and the system will automatically refine and deepen the research until sufficient information is gathered or stopping conditions are met.

The system implements a **Quality-Based Revision Loop** where the Reviewer agent evaluates research quality and triggers automatic revision if quality thresholds are not met. This ensures that reports are only generated when sufficient verified sources are available.

### 12.2 Quality-Based Revision Loop Workflow

The implemented revision loop uses a **quality threshold** (minimum verified sources) rather than confidence scores. The Reviewer agent checks quality after verification and triggers revision if insufficient.

```
User Query: "State of EV batteries in 2026"
    ↓
[Iteration 1]
    ↓
Research Agent → Generate search queries → Collect initial sources
    ↓
Reviewer Agent → Verify sources → Found 0 verified sources
    ↓
[Quality Check: 0 < 2 (minimum required)]
    ↓
[Status: NEEDS_REVISION] → Clear sources & queries → Loop back to Research
    ↓
[Iteration 2]
    ↓
Research Agent → Generate new search queries (using error_message feedback)
    ↓
Reviewer Agent → Verify sources → Found 1 verified source
    ↓
[Quality Check: 1 < 2 (minimum required)]
    ↓
[Status: NEEDS_REVISION] → Clear sources & queries → Loop back to Research
    ↓
[Iteration 3]
    ↓
Research Agent → Generate refined queries
    ↓
Reviewer Agent → Verify sources → Found 3 verified sources
    ↓
[Quality Check: 3 >= 2 (minimum required) ✓]
    ↓
[Status: REVIEWING → Continue to Writer]
    ↓
Writer Agent → Generate comprehensive report with verified sources
```

### 12.2.1 Quality Threshold Mechanism

**Quality Threshold**: Minimum 2 verified sources required (configurable)

**Decision Logic** (in `review_node`):
```python
min_verified_sources = 2  # Quality threshold
verified_count = len(verified_sources)

if verified_count < min_verified_sources:
    if iteration_count >= max_iterations:
        # Proceed anyway if max iterations reached
        continue_to_write()
    else:
        # Trigger revision loop
        return {
            "status": ResearchStatus.NEEDS_REVISION,
            "iteration_count": iteration_count + 1,
            "error_message": f"Insufficient verified sources (found {verified_count}/{min_verified_sources}). Try broader search terms.",
            "sources": [],  # Clear bad sources
            "search_queries": [],  # Clear old queries
            "verified_sources": []  # Clear verified sources
        }
```

### 12.2.2 State Clearing on Revision

When revision is triggered, the following state is cleared to allow fresh research:
- **sources**: Cleared to prevent reusing low-quality sources
- **search_queries**: Cleared to force generation of new queries
- **verified_sources**: Cleared to start verification from scratch
- **conflicting_claims**: Cleared

**Preserved State**:
- **query**: Original user query (preserved)
- **query_id**: Session identifier (preserved)
- **iteration_count**: Incremented to track iterations
- **error_message**: Set with feedback for next research iteration
- **max_iterations**: Preserved to prevent infinite loops

### 12.3 Recursive Research State Model
```python
class RecursiveResearchState(ResearchState):
    """Extended state for recursive research loop"""
    
    # Recursive Research Fields
    iteration_count: int = Field(default=0, ge=0)
    max_iterations: int = Field(default=5, ge=1, le=10)
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Iteration History
    iteration_history: List[dict] = Field(
        default_factory=list,
        description="History of each iteration with queries, sources, confidence"
    )
    
    # Gap Analysis
    knowledge_gaps: List[str] = Field(
        default_factory=list,
        description="Identified gaps in current research that need refinement"
    )
    
    # Refinement Strategy
    refinement_strategy: Optional[Literal["broaden", "deepen", "verify", "complete"]] = Field(
        default=None,
        description="Strategy for next iteration"
    )
```

### 12.4 Recursive Research Logic

#### 12.4.1 Iteration Decision Function
```python
def should_continue_research(
    state: RecursiveResearchState,
    current_confidence: float,
    sources_count: int
) -> tuple[bool, str]:
    """
    Determines if research should continue to next iteration.
    
    Args:
        state: Current research state
        current_confidence: Confidence score from reviewer
        sources_count: Number of verified sources
        
    Returns:
        tuple[bool, str]: (should_continue, reason)
            - should_continue: True if another iteration is needed
            - reason: Explanation for decision
    """
    # Stopping conditions:
    # 1. Confidence >= threshold
    if current_confidence >= state.confidence_threshold:
        return False, "Confidence threshold reached"
    
    # 2. Max iterations reached
    if state.iteration_count >= state.max_iterations:
        return False, "Maximum iterations reached"
    
    # 3. No new sources found in last iteration
    if state.iteration_count > 0:
        last_iteration = state.iteration_history[-1]
        if last_iteration.get("new_sources_count", 0) == 0:
            return False, "No new sources found"
    
    # 4. Confidence not improving
    if state.iteration_count >= 2:
        recent_confidences = [
            it["confidence"] 
            for it in state.iteration_history[-2:]
        ]
        if len(recent_confidences) == 2 and recent_confidences[0] >= recent_confidences[1]:
            return False, "Confidence not improving"
    
    # Continue research
    return True, "Continuing to improve research quality"
```

#### 12.4.2 Query Refinement Strategy
```python
async def refine_search_queries(
    original_query: str,
    iteration_history: List[dict],
    knowledge_gaps: List[str],
    llm_client: Optional[Any] = None
) -> List[str]:
    """
    Generates refined search queries based on previous iterations.
    
    Args:
        original_query: Original user query
        iteration_history: History of previous iterations
        knowledge_gaps: Identified gaps in current research
        llm_client: LLM client for query generation
        
    Returns:
        List[str]: Refined search queries for next iteration
    """
    # Strategy 1: Address knowledge gaps
    if knowledge_gaps:
        gap_queries = [
            f"{original_query} {gap}" 
            for gap in knowledge_gaps[:3]
        ]
        return gap_queries
    
    # Strategy 2: Deepen existing topics
    if iteration_history:
        last_sources = iteration_history[-1].get("sources", [])
        # Extract topics from sources and create deeper queries
        # ...
    
    # Strategy 3: Broaden scope
    # Generate related queries to cover more ground
    # ...
    
    pass
```

#### 12.4.3 Gap Analysis
```python
async def identify_knowledge_gaps(
    query: str,
    verified_sources: List[Source],
    llm_client: Optional[Any] = None
) -> List[str]:
    """
    Identifies gaps in current research that need to be addressed.
    
    Args:
        query: Original research query
        verified_sources: Currently verified sources
        llm_client: LLM client for analysis
        
    Returns:
        List[str]: List of knowledge gaps to address
    """
    # Use LLM to analyze:
    # 1. What aspects of the query are well-covered
    # 2. What aspects are missing or weak
    # 3. What related topics should be explored
    pass
```

### 12.5 LangGraph Quality-Based Revision Workflow

The implemented workflow uses a simpler structure where the review node directly triggers revision:

```python
def create_research_graph() -> StateGraph:
    """
    Creates LangGraph workflow with quality-based revision loop.
    
    Graph Structure:
        START
          ↓
        [research_node]
          ↓
        [review_node] → (quality check)
          ├─→ [research_node] (if NEEDS_REVISION and iterations < max)
          └─→ [write_node] → END (if quality OK or max iterations)
    """
    graph = StateGraph(GraphState)
    
    # Add nodes
    graph.add_node("research", research_node)
    graph.add_node("review", review_node)
    graph.add_node("write", write_node)
    graph.add_node("error_handler", error_handler_node)
    
    # Set entry point
    graph.set_entry_point("research")
    
    # Conditional edge: research → review or error
    graph.add_conditional_edges(
        "research",
        _should_continue,
        {
            "continue": "review",
            "error": "error_handler"
        }
    )
    
    # Conditional edge: review → research (revision) or write or error
    graph.add_conditional_edges(
        "review",
        _review_decision,
        {
            "needs_revision": "research",  # Loop back for revision
            "continue": "write",
            "error": "error_handler"
        }
    )
    
    # Conditional edge: write → end or error
    graph.add_conditional_edges(
        "write",
        _should_continue,
        {
            "continue": END,
            "error": "error_handler"
        }
    )
    
    graph.add_edge("error_handler", END)
    
    return graph.compile()
```

**Key Differences from Original Design**:
- No separate `decision_node` or `refine_node` - decision logic is in `review_node`
- Revision triggered by `NEEDS_REVISION` status, not confidence threshold
- State clearing happens in `review_node` when revision is needed
- Simpler workflow with fewer nodes but same functionality

### 12.6 Quality-Based Revision UI Feedback

The UI must show revision loop progress:
- **Iteration counter**: "Research iteration 2 of 5"
- **Quality status**: "Verified sources: 1/2 (minimum required)"
- **Revision feedback**: Display `error_message` from state when revision is triggered
- **Status indicators**: Show "NEEDS_REVISION" status with explanation
- **Progress**: "Retrying with broader search terms..." when revision loop activates

**StreamEvent Types for Revision**:
- `event_type="status"` with `data={"status": "needs_revision", "message": error_message}`
- Emitted when review_node detects insufficient quality

### 12.7 Integration with Existing System

#### 12.7.1 Current Implementation Status
✅ **Implemented**: Quality-based revision loop with minimum 2 verified sources threshold
✅ **Implemented**: NEEDS_REVISION status in ResearchStatus enum
✅ **Implemented**: Conditional edge from review → research in LangGraph workflow
✅ **Implemented**: State clearing (sources, search_queries, verified_sources) on revision
✅ **Implemented**: Max iterations check to prevent infinite loops
✅ **Implemented**: Fallback mode (non-LangGraph) supports revision loop

#### 12.7.2 Configuration Integration
The quality threshold is currently hardcoded in `review_node`:
```python
min_verified_sources = 2  # Currently hardcoded
```

**Recommended Refactoring**: Move to Config class:
```python
# In src/utils/config.py
class Config:
    # Quality Threshold Settings
    MIN_VERIFIED_SOURCES: int = 2  # Minimum verified sources required
    QUALITY_CHECK_ENABLED: bool = True  # Enable/disable quality checks
```

#### 12.7.3 State Model Alignment
The current `ResearchState` model in `src/models.py` supports the revision loop:
- ✅ `iteration_count`: Tracks iterations
- ✅ `max_iterations`: Prevents infinite loops
- ✅ `status`: Supports NEEDS_REVISION
- ✅ `error_message`: Stores feedback for next iteration

**No refactoring needed** - model already supports revision loop.

#### 12.7.4 Orchestrator Integration
The orchestrator (`src/agents/orchestrator.py`) properly handles:
- ✅ Conditional edge routing based on `_review_decision()`
- ✅ Max iterations check before allowing revision
- ✅ Fallback mode with revision loop support
- ✅ Proper state preservation during revision

**No refactoring needed** - orchestrator correctly implements revision loop.

### 12.8 Refactoring Recommendations

#### 12.8.1 High Priority Refactoring

1. **Make Quality Threshold Configurable**
   - **Current**: Hardcoded `min_verified_sources = 2` in `review_node`
   - **Recommended**: Add to `Config` class and load from environment
   - **Impact**: Allows users to adjust quality requirements
   - **File**: `src/agents/reviewer_agent.py:155`, `src/utils/config.py`

2. **Enhance Error Messages for Research Agent**
   - **Current**: Generic message "Try broader search terms"
   - **Recommended**: More specific feedback based on failure reason
   - **Impact**: Better query refinement in next iteration
   - **File**: `src/agents/reviewer_agent.py:171`

3. **Add Revision Loop Metrics**
   - **Current**: No logging/metrics for revision frequency
   - **Recommended**: Track revision triggers, success rate, iteration patterns
   - **Impact**: Better observability and debugging
   - **File**: `src/agents/reviewer_agent.py`, `src/utils/logger.py`

#### 12.8.2 Medium Priority Enhancements

4. **Consider Confidence-Based Revision (Future)**
   - **Current**: Uses source count threshold only
   - **Future**: Could combine with confidence score threshold
   - **Impact**: More nuanced quality assessment
   - **Note**: Current implementation is simpler and effective

5. **Query Refinement Based on Error Message**
   - **Current**: Research agent doesn't explicitly use `error_message` for refinement
   - **Recommended**: Research agent should analyze `error_message` to improve queries
   - **Impact**: Better query generation in revision iterations
   - **File**: `src/agents/research_agent.py`

6. **Preserve Partial Results Option**
   - **Current**: All sources cleared on revision
   - **Future**: Option to preserve high-quality sources across iterations
   - **Impact**: Avoid re-verifying good sources
   - **Note**: Current approach ensures fresh research, which may be preferable

#### 12.8.3 Low Priority / Future Enhancements

7. **Adaptive Quality Threshold**
   - **Future**: Adjust threshold based on query complexity or domain
   - **Impact**: More flexible quality requirements

8. **Revision Strategy Selection**
   - **Future**: Choose refinement strategy (broaden, deepen, verify) based on failure type
   - **Impact**: More intelligent revision approach

### 12.9 Testing Requirements

#### 12.9.1 Revision Loop Test Cases

1. **Insufficient Sources Test**
   - Input: Query that returns 0 verified sources
   - Expected: Status → NEEDS_REVISION, loop back to research
   - Verify: State cleared, iteration_count incremented

2. **Max Iterations Test**
   - Input: Query that consistently fails quality check
   - Expected: After max_iterations, proceed to write despite low quality
   - Verify: No infinite loop, graceful degradation

3. **Successful Revision Test**
   - Input: Query that fails first iteration, succeeds second
   - Expected: Revision triggered, then proceeds to write
   - Verify: Final report includes verified sources from second iteration

4. **State Preservation Test**
   - Input: Revision triggered
   - Expected: query, query_id, max_iterations preserved
   - Verify: sources, search_queries, verified_sources cleared

5. **Error Message Propagation Test**
   - Input: Revision triggered with error_message
   - Expected: Error message available for next research iteration
   - Verify: Research agent can use error_message for query refinement

---

## 13. True Agentic Intelligence Architecture (Phase 7)

### 13.1 Overview
Phase 7 implements "True Agentic Intelligence" by enabling agents to learn from feedback and use LLM-based verification. This eliminates "blind retries" where the system would repeat the same queries, and replaces simple math-based verification with intelligent LLM-based content analysis.

### 13.2 Key Improvements

#### 13.2.1 Research Agent: Learning from Feedback
**Before (Blind Retries)**:
- Research agent ignored error messages from reviewer
- Generated same queries on each iteration
- No adaptation based on previous failures

**After (True Agentic)**:
- Research agent reads `error_message` from state
- Passes error message as `context` to `generate_search_queries`
- LLM generates DIFFERENT queries based on feedback
- Adapts search strategy (broader terms, synonyms, sub-questions)

#### 13.2.2 Reviewer Agent: LLM-Based Verification
**Before (Math-Based)**:
- Trusted search engine relevance scores blindly
- Simple threshold checks (snippet length ≥20 chars)
- No content quality analysis

**After (True Agentic)**:
- Uses LLM to verify if snippet contains specific facts/data
- Distinguishes between real content and generic SEO spam
- Hard filter: snippet must be ≥50 characters (increased from 20)
- Fallback to relevance score if LLM unavailable

### 13.3 Implementation Details

#### 13.3.1 Research Agent Changes

**Function Signature Update**:
```python
# Before
async def generate_search_queries(
    query: str,
    context: Optional[List[str]] = None,  # List of previous queries
    max_queries: int = 5
) -> List[str]

# After
async def generate_search_queries(
    query: str,
    context: Optional[str] = None,  # Error message from reviewer
    max_queries: int = 5,
    llm_client: Optional[Any] = None  # Required for intelligence
) -> List[str]
```

**Prompt Engineering**:
```
Task: Generate {max_queries} Google search queries for the topic: "{query}"

Context from previous attempt: {context if context else "First attempt"}

CRITICAL INSTRUCTION:
If the context mentions "Insufficient sources", you MUST generate DIFFERENT queries than before. 
Try broader terms, synonyms, or break the topic into smaller sub-questions.

Return only {max_queries} lines. No numbers, no bullets, just one query per line.
```

**Error Message Flow**:
```
Reviewer Agent → Sets error_message in state
    ↓
Research Agent → Captures error_message from state
    ↓
generate_search_queries → Receives error_message as context
    ↓
LLM → Generates DIFFERENT queries based on feedback
```

#### 13.3.2 Reviewer Agent Changes

**Verification Process**:
```python
async def verify_source(source: Source, query: str, llm_client: Optional[Any] = None):
    # 1. HARD FILTER: Garbage Snippets
    if not source.snippet or len(source.snippet) < 50:  # Increased from 20
        return False, 0.0
    
    # 2. INTELLIGENT FILTER: Ask the LLM
    if not llm_client:
        # Fallback to relevance score check
        return source.relevance_score > 0.4, source.relevance_score
    
    # Use LLM to verify if snippet actually answers the query
    prompt = f"""Verify if this text answers the query: "{query}"
Text: "{source.snippet}"

Return YES only if the text contains specific facts/data. Return NO if it is generic SEO spam."""
    
    response = await llm_client.ainvoke(prompt)  # Async call
    content = response.content if hasattr(response, 'content') else str(response)
    is_valid = "YES" in content.upper()
    return is_valid, 0.9 if is_valid else 0.1
```

**LLM Integration**:
- `review_node` loads LLM client using `create_llm_client()`
- Passes LLM client to `verify_source()` for each source
- Uses `ainvoke()` for proper async handling
- Fallback to relevance score if LLM unavailable or fails

### 13.4 Integration with Existing System

#### 13.4.1 LLM Client Integration
Both agents use the same LLM client factory:
```python
from ..utils.llm_client import create_llm_client

try:
    llm_client = create_llm_client()
except Exception as e:
    logger.warning(f"Could not create LLM client: {e}. Using fallback.")
    llm_client = None
```

#### 13.4.2 Error Message Propagation
The revision loop now includes intelligent feedback:
1. **Reviewer** sets `error_message` when quality threshold not met
2. **Research** captures `error_message` from state
3. **Research** passes `error_message` as `context` to query generator
4. **LLM** generates different queries based on feedback

#### 13.4.3 Async LLM Calls
All LLM calls use async patterns:
- `await llm_client.ainvoke(prompt)` for query generation
- `await llm_client.ainvoke(prompt)` for source verification
- Proper error handling with fallbacks

### 13.5 Benefits

1. **Eliminates Blind Retries**: System learns from failures and adapts
2. **Better Query Generation**: LLM generates contextually appropriate queries
3. **Quality Source Verification**: Distinguishes real content from spam
4. **Reduced False Positives**: Hard filter (50 chars) + LLM verification
5. **Graceful Degradation**: Fallbacks if LLM unavailable

### 13.6 Performance Considerations

#### 13.6.1 API Usage
- **Query Generation**: 1 LLM call per research iteration
- **Source Verification**: 1 LLM call per source (can be expensive)
- **Recommendation**: Consider caching or batch verification (future enhancement)

#### 13.6.2 Latency Impact
- **Query Generation**: Adds ~1-2 seconds per iteration
- **Source Verification**: Adds ~0.5-1 second per source
- **Mitigation**: Concurrent verification with `asyncio.gather()` (future)

### 13.7 Refactoring Recommendations

#### 13.7.1 High Priority

1. **Batch Source Verification**
   - **Current**: Verifies sources one-by-one
   - **Recommended**: Batch multiple sources in single LLM call
   - **Impact**: Reduces API calls and latency
   - **File**: `src/agents/reviewer_agent.py`

2. **Cache LLM Verification Results**
   - **Current**: Verifies same source multiple times if revision occurs
   - **Recommended**: Cache verification results by URL hash
   - **Impact**: Reduces redundant API calls
   - **File**: `src/agents/reviewer_agent.py`, `src/utils/cache.py` (new)

3. **Monitor API Usage**
   - **Current**: No tracking of LLM API usage/costs
   - **Recommended**: Add metrics for LLM calls per query
   - **Impact**: Better cost visibility
   - **File**: `src/utils/logger.py`, `src/utils/metrics.py` (new)

#### 13.7.2 Medium Priority

4. **Improve Error Message Specificity**
   - **Current**: Generic "Try broader search terms"
   - **Recommended**: More specific feedback (e.g., "Try synonyms for X", "Break into sub-questions")
   - **Impact**: Better query refinement
   - **File**: `src/agents/reviewer_agent.py:193`

5. **Adaptive Snippet Threshold**
   - **Current**: Fixed 50 character threshold
   - **Recommended**: Adjust based on query complexity or domain
   - **Impact**: More flexible filtering

6. **Query Generation Caching**
   - **Current**: Generates queries fresh each time
   - **Recommended**: Cache query generation for same query+context
   - **Impact**: Reduces redundant LLM calls

### 13.8 Testing Requirements

#### 13.8.1 Query Generation Tests

1. **Error Message Context Test**
   - Input: Query with error_message "Insufficient sources"
   - Expected: LLM generates DIFFERENT queries than first attempt
   - Verify: Queries are broader/different from original

2. **Fallback Test**
   - Input: LLM unavailable
   - Expected: Falls back to simple query variations
   - Verify: System still functions without LLM

3. **Query Parsing Test**
   - Input: LLM returns numbered list or bullet points
   - Expected: Properly parses queries from various formats
   - Verify: All queries extracted correctly

#### 13.8.2 Source Verification Tests

1. **LLM Verification Test**
   - Input: Source with specific facts vs generic SEO spam
   - Expected: LLM correctly identifies quality sources
   - Verify: High-quality sources pass, spam rejected

2. **Hard Filter Test**
   - Input: Source with snippet < 50 characters
   - Expected: Rejected before LLM call
   - Verify: No unnecessary LLM calls

3. **Fallback Test**
   - Input: LLM unavailable or fails
   - Expected: Falls back to relevance score check
   - Verify: System still functions without LLM

4. **Async Handling Test**
   - Input: Multiple sources to verify
   - Expected: All verifications complete without blocking
   - Verify: Proper async execution

---

## 14. Architecture Documentation References

### 14.1 Supporting Documentation
The following architecture documents should be created in `docs/architecture/`:

1. **`ARCHITECTURE_OVERVIEW.md`**
   - High-level system architecture
   - Key design decisions and rationale
   - Technology choices and trade-offs
   - Cross-references to detailed specs

2. **`DATA_FLOW.md`**
   - Detailed data flow diagrams
   - State transitions
   - Event streaming patterns
   - Async operation flows

3. **`AGENT_WORKFLOW.md`**
   - Recursive research process documentation
   - Agent interaction patterns
   - Decision logic for iterations
   - Stopping conditions and thresholds

4. **`STATE_MANAGEMENT.md`**
   - ResearchState model deep dive
   - Session state isolation
   - Concurrent query handling
   - State persistence patterns

### 14.2 Cross-References
- Section 2.1 (ResearchState) → `docs/architecture/STATE_MANAGEMENT.md`
- Section 5 (Async Data Flow) → `docs/architecture/DATA_FLOW.md`
- Section 12 (Recursive Research) → `docs/architecture/AGENT_WORKFLOW.md`
- Section 1 (System Architecture) → `docs/architecture/ARCHITECTURE_OVERVIEW.md`

---

## 15. Implementation Checklist Reference

This specification supports the following TODO.md tasks:

### Phase 6: Quality-Based Revision Loop ✅ COMPLETED

- ✅ **Task 6.1**: Revision Loop Mechanism
  - ✅ NEEDS_REVISION status added to ResearchStatus enum
  - ✅ Quality check logic in review_node (minimum 2 verified sources)
  - ✅ State clearing on revision trigger
  - ✅ Iteration count tracking
  
- ✅ **Task 6.2**: Orchestrator Integration
  - ✅ Conditional edge from review → research for revision loop
  - ✅ Max iterations check to prevent infinite loops
  - ✅ Fallback mode supports revision loop
  
- ✅ **Task 6.3**: State Management
  - ✅ Iteration count properly tracked
  - ✅ State clearing (sources, search_queries) on revision
  - ✅ Query and query_id preserved during revision
  - ✅ Error message set with feedback

**Documentation Status**: ✅ Fully documented in Section 12 (Recursive Research Loop Architecture)

### Phase 7: True Agentic Intelligence ✅ COMPLETED

- ✅ **Task 7.1**: Research Agent - Stop Blind Retries
  - ✅ `generate_search_queries` accepts `context` as `str` (error message)
  - ✅ LLM-based query generation with feedback-aware prompts
  - ✅ `research_node` captures `error_message` from state
  - ✅ Passes `error_message` as context to query generator
  - ✅ LLM client loaded in `research_node` for intelligent generation
  
- ✅ **Task 7.2**: Reviewer Agent - Add LLM Brain
  - ✅ `verify_source` uses LLM for intelligent verification
  - ✅ Snippet threshold increased from 20 to 50 characters
  - ✅ LLM prompt checks for specific facts/data vs SEO spam
  - ✅ Fallback to relevance score if LLM fails
  - ✅ `review_node` loads and passes LLM client
  - ✅ Async LLM calls use `ainvoke` for proper handling

**Documentation Status**: ✅ Fully documented in Section 13 (True Agentic Intelligence Architecture)

### Phase 8: Performance Optimization & Enhanced Intelligence 🔄 PENDING

**Feature**: Performance Optimization, Caching, and Enhanced Intelligence

**Status**: 🔄 **PENDING** - Follow-up tasks from Phase 7 Feature Audit

- [ ] **Task 8.1.1**: Batch Source Verification
  - [ ] Create `verify_sources_batch()` function
  - [ ] Reduce API calls from N to N/batch_size
  - [ ] Maintain backward compatibility with fallback
  
- [ ] **Task 8.1.2**: Cache LLM Verification Results
  - [ ] Create `src/utils/cache.py` with `VerificationCache` class
  - [ ] Cache by URL hash with 24-hour TTL
  - [ ] Integrate with `verify_source()` function
  
- [ ] **Task 8.1.3**: Monitor API Usage & Costs
  - [ ] Create `src/utils/metrics.py` with metrics tracking
  - [ ] Track LLM calls, tokens, costs per query
  - [ ] Add metrics to final state
  
- [ ] **Task 8.1.4**: Make Quality Threshold Configurable
  - [ ] Add `MIN_VERIFIED_SOURCES` to Config class
  - [ ] Update `review_node()` to use config value
  - [ ] Add to `.env.example`
  
- [ ] **Task 8.1.5**: Enhance Error Messages
  - [ ] Create `generate_revision_feedback()` function
  - [ ] Analyze failure reasons intelligently
  - [ ] Generate specific, actionable suggestions
  
- [ ] **Task 8.1.6**: Add Revision Loop Metrics
  - [ ] Log revision triggers with context
  - [ ] Track revision patterns and success rates
  - [ ] Add to metrics collector

**Documentation Status**: ✅ Fully documented in Section 18 (Phase 8 Architecture)

- ✅ **Task 7.1**: Research Agent - Stop Blind Retries
  - ✅ `generate_search_queries` accepts `context` as `str` (error message)
  - ✅ LLM-based query generation with feedback-aware prompts
  - ✅ `research_node` captures `error_message` from state
  - ✅ Passes `error_message` as context to query generator
  - ✅ LLM client loaded in `research_node` for intelligent generation
  
- ✅ **Task 7.2**: Reviewer Agent - Add LLM Brain
  - ✅ `verify_source` uses LLM for intelligent verification
  - ✅ Snippet threshold increased from 20 to 50 characters
  - ✅ LLM prompt checks for specific facts/data vs SEO spam
  - ✅ Fallback to relevance score if LLM fails
  - ✅ `review_node` loads and passes LLM client
  - ✅ Async LLM calls use `ainvoke` for proper handling

**Documentation Status**: ✅ Fully documented in Section 13 (True Agentic Intelligence Architecture)

### Phase 2: Architecture Design & Documentation

#### Task 2.1: Architecture Review & Specification Update
- ✅ **Sub-task 2.1.1**: ResearchState Model Compliance
  - Model includes all required fields (query, sources, draft_report, status, query_id)
  - Supports recursive research loop (iteration_count, max_iterations, iteration_history)
  - Decoupled from UI rendering (pure Pydantic model)
  
- ✅ **Sub-task 2.1.2**: Async Data Flow Architecture
  - All external API calls marked as async
  - Uses asyncio and st.rerun() patterns
  - Concurrent searches use asyncio.gather()
  - Explicit documentation of UI freezing prevention (Section 5.3.1)
  
- ✅ **Sub-task 2.1.3**: Streaming Mechanism Specification
  - StreamEvent model defined with proper event types
  - Async-safe UI update mechanism documented
  - Rate limiting to prevent UI flooding
  
- ✅ **Sub-task 2.1.4**: Agent Architecture
  - Research, Reviewer, and Writer agents defined
  - Clear responsibilities and contracts
  - LangGraph workflow orchestration specified
  - Recursive research loop defined (Section 12)
  
- ✅ **Sub-task 2.1.5**: Error Handling & State Management
  - Error handling patterns address @Coder_Standards
  - User-friendly error messages with templates (Section 8.3)
  - State isolation for concurrent queries (Section 5.3.2)
  - Error recovery strategies defined
  
- ✅ **Sub-task 2.1.6**: Secret Isolation Compliance
  - Configuration loading prioritizes st.secrets then .env
  - No hardcoded API keys allowed
  - ConfigError raised if keys missing
  - Explicit prohibition documented (Section 3.3.1)
  
- ✅ **Sub-task 2.1.7**: Recursive Research Loop Specification
  - Recursive research workflow documented (Section 12)
  - Iteration logic and stopping conditions defined
  - Query refinement strategies specified
  - Gap analysis mechanism described
  
- ✅ **Sub-task 2.1.8**: Architecture Documentation Summary
  - References to architecture docs created (Section 13)
  - Cross-references to detailed documentation
  
- ✅ **Sub-task 2.1.9**: Final Architecture Review
  - All @Architect_Rules addressed
  - All @Orchestrator_Tasks requirements met
  - Specification is complete and consistent

---

## 16. Phase 7: True Agentic Intelligence Integration Summary

### 16.1 Feature Overview
Phase 7 implements "True Agentic Intelligence" by enabling agents to learn from feedback and use LLM-based verification. This eliminates blind retries and replaces simple math-based checks with intelligent content analysis.

### 16.2 Integration Points

1. **Research Agent** (`src/agents/research_agent.py`)
   - ✅ `generate_search_queries()` accepts `context` as `str` (error message)
   - ✅ LLM-based query generation with feedback-aware prompts
   - ✅ `research_node()` captures `error_message` and passes to query generator
   - ✅ LLM client loaded in `research_node()` for intelligent generation

2. **Reviewer Agent** (`src/agents/reviewer_agent.py`)
   - ✅ `verify_source()` uses LLM for intelligent verification
   - ✅ Hard filter: snippet threshold increased to 50 characters
   - ✅ LLM prompt distinguishes facts/data from SEO spam
   - ✅ Fallback to relevance score if LLM unavailable
   - ✅ `review_node()` loads and passes LLM client to `verify_source()`

3. **LLM Client** (`src/utils/llm_client.py`)
   - ✅ Both agents use `create_llm_client()` factory
   - ✅ Proper async handling with `ainvoke()`
   - ✅ Error handling with graceful fallbacks

### 16.3 Key Design Decisions

1. **Context Type Change**: `List[str]` → `str` for error messages (simpler, more direct)
2. **LLM Integration**: Required for intelligence, but with fallbacks for reliability
3. **Hard Filter First**: Check snippet length before expensive LLM call
4. **Async LLM Calls**: All LLM operations use `ainvoke()` for non-blocking execution

### 16.4 Refactoring Opportunities

**High Priority**:
1. Batch source verification to reduce API calls
2. Cache LLM verification results by URL
3. Monitor API usage/costs for LLM calls

**Medium Priority**:
4. Improve error message specificity for better query refinement
5. Adaptive snippet threshold based on query complexity
6. Query generation caching for same query+context

See Section 13.7 for detailed refactoring recommendations.

---

## 17. Quality-Based Revision Loop Integration Summary

### 17.1 Feature Overview
The Quality-Based Revision Loop (Phase 6) has been successfully implemented and integrated into the Deep Research Assistant system. This feature ensures that research reports are only generated when sufficient verified sources are available, automatically triggering revision when quality thresholds are not met.

### 17.2 Integration Points

1. **Data Models** (`src/models.py`)
   - ✅ `ResearchStatus.NEEDS_REVISION` enum value added
   - ✅ `ResearchState` model already supports all required fields

2. **Reviewer Agent** (`src/agents/reviewer_agent.py`)
   - ✅ Quality check implemented in `review_node()` (line 154-178)
   - ✅ Minimum 2 verified sources threshold (hardcoded, recommended for refactoring)
   - ✅ State clearing logic when revision triggered

3. **Orchestrator** (`src/agents/orchestrator.py`)
   - ✅ `_review_decision()` function handles NEEDS_REVISION routing (line 119-142)
   - ✅ Conditional edge from review → research for revision loop (line 87-95)
   - ✅ Max iterations check prevents infinite loops
   - ✅ Fallback mode supports revision loop (line 260-275)

4. **Workflow Graph**
   - ✅ LangGraph workflow includes revision loop edge
   - ✅ Both LangGraph and fallback modes support revision

### 15.3 Key Design Decisions

1. **Quality Threshold**: Minimum 2 verified sources (simpler than confidence-based)
2. **State Clearing**: All sources/queries cleared on revision (ensures fresh research)
3. **Decision Location**: Quality check in `review_node` (simpler than separate decision node)
4. **Max Iterations**: Prevents infinite loops, allows graceful degradation

### 17.4 Refactoring Opportunities

**High Priority**:
1. Make quality threshold configurable via `Config` class
2. Enhance error messages for better query refinement
3. Add revision loop metrics/logging

**Medium Priority**:
4. Research agent should use `error_message` for query refinement
5. Consider preserving high-quality sources across iterations

See Section 12.8 for detailed refactoring recommendations.

---

## 18. Phase 8: Performance Optimization & Enhanced Intelligence Architecture

### 18.1 Overview
Phase 8 addresses performance optimizations, caching strategies, and enhanced intelligence features identified during the Phase 7 feature audit. These improvements focus on reducing API costs, improving latency, and enhancing the agentic capabilities of the system.

### 18.2 High Priority Optimizations

#### 18.2.1 Batch Source Verification
**Current Issue**: Verifies sources one-by-one, causing N LLM API calls for N sources.

**Solution**: Batch multiple sources in a single LLM call.

**API Signature**:
```python
# File: src/agents/reviewer_agent.py

async def verify_sources_batch(
    sources: List[Source],
    query: str,
    llm_client: Optional[Any] = None,
    batch_size: int = 10
) -> List[Tuple[Source, bool, float]]:
    """
    Verifies multiple sources in a single LLM call for efficiency.
    
    Args:
        sources: List of sources to verify
        query: Original research query
        llm_client: LLM client instance
        batch_size: Maximum sources per batch
        
    Returns:
        List[Tuple[Source, bool, float]]: List of (source, is_verified, confidence_score) tuples
        
    Implementation:
        - Groups sources into batches
        - Single LLM call per batch with structured output
        - Returns verification results for all sources
    """
    pass
```

**Integration**:
- Replace individual `verify_source()` calls in `review_node()` with `verify_sources_batch()`
- Maintains same verification logic but reduces API calls from N to N/batch_size
- Fallback to individual verification if batch fails

**Impact**: Reduces API calls and latency significantly (e.g., 10 sources = 1 call instead of 10).

#### 18.2.2 Cache LLM Verification Results
**Current Issue**: Verifies same source multiple times if revision occurs.

**Solution**: Cache verification results by URL hash.

**API Signature**:
```python
# File: src/utils/cache.py (new)

from typing import Optional, Tuple
import hashlib
from datetime import datetime, timedelta

class VerificationCache:
    """Cache for LLM verification results"""
    
    def __init__(self, ttl_hours: int = 24):
        """
        Initialize cache with TTL.
        
        Args:
            ttl_hours: Time-to-live in hours (default 24)
        """
        self.cache: dict[str, dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def get(self, url: str) -> Optional[Tuple[bool, float]]:
        """
        Get cached verification result.
        
        Args:
            url: Source URL
            
        Returns:
            Optional[Tuple[bool, float]]: (is_verified, confidence_score) if cached and valid
        """
        cache_key = self._hash_url(url)
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if datetime.now() - entry['timestamp'] < self.ttl:
                return entry['result']
            else:
                del self.cache[cache_key]
        return None
    
    def set(self, url: str, is_verified: bool, confidence_score: float) -> None:
        """
        Cache verification result.
        
        Args:
            url: Source URL
            is_verified: Verification result
            confidence_score: Confidence score
        """
        cache_key = self._hash_url(url)
        self.cache[cache_key] = {
            'result': (is_verified, confidence_score),
            'timestamp': datetime.now()
        }
    
    def _hash_url(self, url: str) -> str:
        """Generate hash key from URL"""
        return hashlib.md5(url.encode()).hexdigest()
```

**Integration**:
- Create `src/utils/cache.py` with `VerificationCache` class
- Update `verify_source()` to check cache before LLM call
- Store results in cache after verification
- TTL: 24 hours (sources may change over time)

**Impact**: Reduces redundant API calls for sources verified in previous iterations.

#### 18.2.3 Monitor API Usage & Costs
**Current Issue**: No tracking of LLM API usage/costs.

**Solution**: Add metrics tracking for LLM calls.

**API Signature**:
```python
# File: src/utils/metrics.py (new)

from typing import Dict, List
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class LLMMetrics:
    """Metrics for LLM API usage"""
    query_id: str
    query_generation_calls: int = 0
    verification_calls: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    timestamps: List[datetime] = field(default_factory=list)
    
    def add_query_generation(self, tokens: int, cost: float) -> None:
        """Record query generation call"""
        self.query_generation_calls += 1
        self.total_tokens += tokens
        self.estimated_cost += cost
        self.timestamps.append(datetime.now())
    
    def add_verification(self, tokens: int, cost: float) -> None:
        """Record verification call"""
        self.verification_calls += 1
        self.total_tokens += tokens
        self.estimated_cost += cost
        self.timestamps.append(datetime.now())

class MetricsCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, LLMMetrics] = {}
    
    def get_metrics(self, query_id: str) -> LLMMetrics:
        """Get or create metrics for query_id"""
        if query_id not in self.metrics:
            self.metrics[query_id] = LLMMetrics(query_id=query_id)
        return self.metrics[query_id]
    
    def get_summary(self) -> Dict:
        """Get summary of all metrics"""
        total_calls = sum(m.query_generation_calls + m.verification_calls 
                         for m in self.metrics.values())
        total_cost = sum(m.estimated_cost for m in self.metrics.values())
        return {
            'total_queries': len(self.metrics),
            'total_llm_calls': total_calls,
            'total_cost': total_cost,
            'avg_cost_per_query': total_cost / len(self.metrics) if self.metrics else 0
        }
```

**Integration**:
- Create `src/utils/metrics.py` with metrics tracking
- Update `generate_search_queries()` to track query generation calls
- Update `verify_source()` to track verification calls
- Add metrics to `ResearchState` model (optional)
- Log metrics summary in final state

**Impact**: Better cost visibility and optimization opportunities.

#### 18.2.4 Configurable Quality Threshold
**Current Issue**: Hardcoded `min_verified_sources = 2` in `review_node`.

**Solution**: Add to `Config` class.

**API Signature**:
```python
# File: src/utils/config.py

class Config:
    # ... existing fields ...
    
    # Quality Threshold Settings
    MIN_VERIFIED_SOURCES: int = Field(
        default=2,
        description="Minimum verified sources required before proceeding to write"
    )
    QUALITY_CHECK_ENABLED: bool = Field(
        default=True,
        description="Enable/disable quality threshold checks"
    )
    
    @classmethod
    def load(cls) -> "Config":
        # ... existing load logic ...
        # Add:
        min_sources = int(os.getenv("MIN_VERIFIED_SOURCES", "2"))
        quality_check = os.getenv("QUALITY_CHECK_ENABLED", "true").lower() == "true"
        # ...
```

**Integration**:
- Update `Config` class in `src/utils/config.py`
- Update `review_node()` to use `config.MIN_VERIFIED_SOURCES`
- Add environment variable `MIN_VERIFIED_SOURCES` to `.env.example`

**Impact**: Allows users to adjust quality requirements based on use case.

#### 18.2.5 Enhanced Error Messages
**Current Issue**: Generic message "Try broader search terms".

**Solution**: Generate specific feedback based on failure analysis.

**API Signature**:
```python
# File: src/agents/reviewer_agent.py

async def generate_revision_feedback(
    verified_count: int,
    min_required: int,
    sources: List[Source],
    query: str,
    llm_client: Optional[Any] = None
) -> str:
    """
    Generates specific feedback for research agent based on failure analysis.
    
    Args:
        verified_count: Number of verified sources found
        min_required: Minimum required sources
        sources: All sources that were checked
        query: Original query
        llm_client: LLM client for intelligent feedback generation
        
    Returns:
        str: Specific feedback message
        
    Examples:
        - "Try synonyms for 'battery technology'"
        - "Break query into sub-questions: 'EV battery capacity' and 'EV battery cost'"
        - "Use more specific terms like 'lithium-ion' instead of 'batteries'"
    """
    # Analyze why sources failed
    # Use LLM to generate specific suggestions
    pass
```

**Integration**:
- Create `generate_revision_feedback()` function
- Replace generic error message in `review_node()` with intelligent feedback
- Analyze failure reasons (snippet too short, LLM rejected, etc.)
- Use LLM to generate actionable suggestions

**Impact**: Better query refinement in next iteration.

#### 18.2.6 Revision Loop Metrics
**Current Issue**: No logging/metrics for revision frequency.

**Solution**: Track revision triggers and patterns.

**API Signature**:
```python
# File: src/agents/reviewer_agent.py

def log_revision_trigger(
    query_id: str,
    iteration_count: int,
    verified_count: int,
    reason: str
) -> None:
    """
    Log revision trigger event for metrics.
    
    Args:
        query_id: Query identifier
        iteration_count: Current iteration number
        verified_count: Number of verified sources found
        reason: Reason for revision (e.g., "insufficient_sources")
    """
    logger.info(
        f"Revision triggered: query_id={query_id}, "
        f"iteration={iteration_count}, verified={verified_count}, reason={reason}"
    )
    # Add to metrics if available
```

**Integration**:
- Add logging in `review_node()` when revision is triggered
- Track: revision trigger reason, iteration count, sources found
- Add metrics to `ResearchState` for analysis
- Create dashboard/report of revision patterns (future)

**Impact**: Better observability and debugging.

### 18.3 Medium Priority Enhancements

#### 18.3.1 Adaptive Snippet Threshold
**Current**: Fixed 50 character threshold.

**Solution**: Adjust based on query complexity.

**Implementation**:
```python
def calculate_snippet_threshold(query: str) -> int:
    """
    Calculate adaptive snippet threshold based on query complexity.
    
    Args:
        query: User query
        
    Returns:
        int: Snippet threshold (30-70 characters)
    """
    # Simple heuristic: longer queries = higher threshold
    word_count = len(query.split())
    if word_count <= 3:
        return 30  # Simple queries
    elif word_count <= 6:
        return 50  # Medium queries (current default)
    else:
        return 70  # Complex queries
```

#### 18.3.2 Query Generation Caching
**Current**: Generates queries fresh each time.

**Solution**: Cache query generation for same query+context.

**Implementation**:
- Create cache key from `hash(query + context)`
- Check cache before LLM call
- TTL: 1 hour (queries may need refresh)
- Store in `VerificationCache` or separate `QueryCache`

#### 18.3.3 Query Refinement Enhancement
**Current**: Research agent doesn't explicitly analyze `error_message`.

**Solution**: Parse error message for specific suggestions.

**Implementation**:
- Parse `error_message` for keywords (e.g., "synonyms", "sub-questions")
- Use suggestions in prompt to LLM
- Generate queries that address specific failure reasons

### 18.4 Integration with Existing System

#### 18.4.1 Caching Infrastructure
- **New File**: `src/utils/cache.py`
  - `VerificationCache` class for source verification results
  - `QueryCache` class for query generation (optional)
  - Shared TTL and cleanup logic

#### 18.4.2 Metrics Infrastructure
- **New File**: `src/utils/metrics.py`
  - `LLMMetrics` dataclass for per-query metrics
  - `MetricsCollector` singleton for aggregation
  - Integration with logger for reporting

#### 18.4.3 Configuration Updates
- **File**: `src/utils/config.py`
  - Add `MIN_VERIFIED_SOURCES` setting
  - Add `QUALITY_CHECK_ENABLED` setting
  - Update `.env.example` with new variables

#### 18.4.4 Agent Updates
- **File**: `src/agents/reviewer_agent.py`
  - Add `verify_sources_batch()` function
  - Update `verify_source()` to use cache
  - Add `generate_revision_feedback()` function
  - Update `review_node()` to use configurable threshold
  - Add revision metrics logging

- **File**: `src/agents/research_agent.py`
  - Add query generation caching (optional)
  - Enhance query refinement based on error messages

### 18.5 Performance Impact Estimates

#### 18.5.1 API Call Reduction
- **Before**: N sources = N LLM calls for verification
- **After (Batch)**: N sources = N/batch_size LLM calls
- **Savings**: ~90% reduction for 10 sources (10 calls → 1 call)

#### 18.5.2 Latency Improvement
- **Before**: Sequential verification = N × avg_call_time
- **After (Batch)**: Batch verification = 1 × batch_call_time
- **Improvement**: ~80% faster for 10 sources

#### 18.5.3 Cost Reduction
- **Before**: No caching, redundant calls
- **After (Cache)**: Cache hits avoid redundant calls
- **Savings**: ~30-50% cost reduction for revision loops

### 18.6 Refactoring Checklist

#### 18.6.1 High Priority (Phase 8.1)
- [ ] **Task 8.1.1**: Implement batch source verification
- [ ] **Task 8.1.2**: Implement LLM verification caching
- [ ] **Task 8.1.3**: Add API usage monitoring
- [ ] **Task 8.1.4**: Make quality threshold configurable
- [ ] **Task 8.1.5**: Enhance error messages
- [ ] **Task 8.1.6**: Add revision loop metrics

#### 18.6.2 Medium Priority (Phase 8.2)
- [ ] **Task 8.2.1**: Implement adaptive snippet threshold
- [ ] **Task 8.2.2**: Add query generation caching
- [ ] **Task 8.2.3**: Enhance query refinement

#### 18.6.3 Testing (Phase 8.3)
- [ ] **Task 8.3.1**: Test batch verification
- [ ] **Task 8.3.2**: Test cache hit/miss scenarios
- [ ] **Task 8.3.3**: Test metrics collection
- [ ] **Task 8.3.4**: Test configurable thresholds

### 18.7 Backward Compatibility

All Phase 8 changes maintain backward compatibility:
- **Batch Verification**: Falls back to individual verification if batch fails
- **Caching**: Optional, doesn't break existing flow
- **Metrics**: Additive, doesn't change core functionality
- **Config**: Defaults match current hardcoded values

---

**Document Version**: 2.3  
**Last Updated**: 2024  
**Status**: Complete - All Architecture Requirements Addressed, Phase 6, 7 & 8 Integration Documented  
**Next Phase**: Skeleton Implementation (Phase 3) / Phase 8 Implementation