# Data Flow & State - Deep Research Assistant

## Async Data Flow

The system uses an asynchronous data flow to ensure the UI remains responsive during long-running research tasks.

### Request Flow
1. **User Input**: Query submitted via Streamlit.
2. **State Initialization**: `ResearchState` object created.
3. **Workflow Execution**: LangGraph workflow started in a background thread.
4. **Agent Updates**: Agents emit `StreamEvent` objects via a callback.
5. **UI Updates**: `StreamEvent` objects update the Streamlit session state and trigger reruns.

## State Management

### ResearchState (`src/models.py`)
The `ResearchState` is the single source of truth for a research session. It tracks:
- Progress Status
- Collected Sources
- Verified Sources
- Confidence Scores
- Draft and Final Reports
- Token Usage & Estimated Cost

### State Isolation
Each query is assigned a unique `query_id` (UUID4) to ensure complete isolation in concurrent environments.
