# Data Flow & State Management

## Async Data Flow
The application uses an asynchronous, event-driven architecture to communicate between the Streamlit frontend and the LangGraph backend.

```mermaid
sequenceDiagram
    participant User
    participant Streamlit as Streamlit UI
    participant Async as Async Loop (Background)
    participant Graph as LangGraph Workflow
    participant Callback as Stream Callback
    
    User->>Streamlit: Enters Query
    Streamlit->>Streamlit: Create Task & Thread
    Streamlit->>Async: Start Workflow execution
    Async->>Graph: run_research_workflow(query, callback)
    
    loop Research Process
        Graph->>Graph: Execute Agent Node
        Graph->>Callback: Emit StreamEvent (status/data)
        Callback->>Streamlit: Update Session State
        Streamlit->>User: Rerender UI (via st.rerun or polling)
    end
    
    Graph->>Async: Return Final State
    Async->>Streamlit: Update Final State
    Streamlit->>User: Show Final Report
```

## State Management
The `ResearchState` Pydantic model is the core data structure passed between agents.

### State Lifecycle
1.  **Initialization**: Created in `src/main.py` when a new query is submitted.
2.  **Processing**: Passed through the LangGraph workflow, where agents modify it (adding sources, updating status).
3.  **Streaming**: Intermediate updates are pushed to the UI via `StreamEvent`.
4.  **Persistence**: Stored in `st.session_state` to survive Streamlit re-runs.

### Concurrency
*   Each query has a unique `query_id`.
*   Session state keys are namespaces with `query_id` to allow multiple concurrent research sessions (if supported by UI).
*   Background threads operate on their own event loops to avoid blocking the main thread.
