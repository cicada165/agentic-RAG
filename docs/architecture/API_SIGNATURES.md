# API Signatures - Deep Research Assistant

## LangGraph Backend API

### Workflow Orchestration
File: `src/agents/orchestrator.py`

#### GraphState
```python
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
```

#### Graph Construction
- `create_research_graph() -> StateGraph`: Creates the LangGraph workflow.
- `run_research_workflow(...) -> ResearchState`: Asynchronous execution entry point.

### Agent Nodes

#### Research Agent (`src/agents/research_agent.py`)
- `research_node(state: GraphState) -> GraphState`: Performs web search and collects sources.
- `generate_search_queries(query: str, context: Optional[str]) -> List[str]`: Intelligent query generation.

#### Reviewer Agent (`src/agents/reviewer_agent.py`)
- `review_node(state: GraphState) -> GraphState`: Fact-checks sources and identifies conflicts.
- `verify_source(source: Source, query: str) -> tuple[bool, float]`: Individual source verification.

#### Writer Agent (`src/agents/writer_agent.py`)
- `write_node(state: GraphState) -> GraphState`: Generates final markdown report.

## Configuration & Utilities

### Configuration
File: `src/utils/config.py`
- `Config.load()`: Prioritizes Streamlit secrets, then environment variables, then `.env`.

### Monitoring
File: `src/utils/monitoring.py`
- `UsageTracker`: Tracks token usage and calculates estimated USD cost.
