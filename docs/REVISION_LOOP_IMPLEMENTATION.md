# Revision Loop Implementation

## Overview

The revision loop mechanism allows the Reviewer Agent to trigger a loop back to the Research Agent when the quality of verified sources is insufficient. This implements the "Recursive Research" requirement from the project goals.

## Implementation Details

### 1. Status Enum Update

Added `NEEDS_REVISION` status to `ResearchStatus` enum in `src/models.py`:

```python
class ResearchStatus(str, Enum):
    # ... existing statuses ...
    NEEDS_REVISION = "needs_revision"  # Triggers loop back to research
```

### 2. Reviewer Agent Quality Check

Updated `review_node` in `src/agents/reviewer_agent.py` to check quality threshold:

**Quality Threshold**: Minimum 2 verified sources required

**Decision Logic**:
- If verified sources < 2 AND iteration_count < max_iterations:
  - Return `needs_revision` status
  - Increment `iteration_count`
  - Clear sources and search_queries
  - Set error_message with feedback
- Otherwise: Proceed to write phase

**State Update on Revision**:
```python
{
    **state,  # Preserve existing state
    "status": "needs_revision",
    "iteration_count": iteration_count + 1,
    "error_message": f"Insufficient verified sources (found {len(verified_sources)}/2). Try broader search terms.",
    "sources": [],  # Clear bad sources
    "search_queries": [],  # Clear old queries
    "current_agent": "reviewer",
    "verified_sources": [],
    "conflicting_claims": [],
    "confidence_score": 0.0
}
```

### 3. Orchestrator Conditional Edge

Updated `src/agents/orchestrator.py` to handle revision loop:

**New Function**: `_review_decision(state)`
- Checks if status is `needs_revision`
- Validates max iterations not exceeded
- Returns routing decision: `"needs_revision"`, `"continue"`, or `"error"`

**Conditional Edge**:
```python
workflow.add_conditional_edges(
    "review",
    _review_decision,
    {
        "continue": "write",
        "needs_revision": "research",  # Loop back to research
        "error": "error_handler"
    }
)
```

### 4. Fallback Mode Support

Updated fallback mode (non-LangGraph execution) to support revision loop:

- Implements while loop with max_iterations check
- Handles `needs_revision` status
- Emits appropriate stream events
- Continues loop until quality passes or max iterations reached

## Workflow Diagram

```
Research → Review → [Quality Check]
                      │
                      ├─ Quality OK → Write → End
                      │
                      └─ Quality Low → [Check Iterations]
                                         │
                                         ├─ < Max → Research (loop)
                                         │
                                         └─ >= Max → Write (proceed anyway)
```

## Configuration

- **Min Verified Sources**: 2 (hardcoded, can be made configurable)
- **Max Iterations**: 5 (default, from `max_iterations` in state)
- **Quality Threshold**: Can be adjusted in `review_node` logic

## Safety Features

1. **Iteration Counter**: Prevents infinite loops
2. **Max Iterations Check**: Proceeds to write even if quality is low after max iterations
3. **State Cleanup**: Clears bad sources/queries on revision
4. **Error Messages**: Provides feedback for next research iteration

## Future Enhancements

1. **Configurable Threshold**: Make min_verified_sources configurable via Config
2. **Enhanced Feedback**: Use error_message to guide research agent's next search
3. **Metrics**: Track revision loop frequency and success rates
4. **Adaptive Thresholds**: Adjust quality requirements based on query complexity

## Testing

To test the revision loop:

1. **Scenario 1**: Query that returns insufficient sources
   - Expected: Loop back to research
   - Check: iteration_count increments
   - Check: sources cleared

2. **Scenario 2**: Max iterations reached
   - Expected: Proceed to write despite low quality
   - Check: Final state has iteration_count == max_iterations

3. **Scenario 3**: Quality passes on first try
   - Expected: No loop, proceed directly to write
   - Check: iteration_count remains 0 or 1

## Files Modified

- `src/models.py` - Added NEEDS_REVISION status
- `src/agents/reviewer_agent.py` - Added quality check and revision logic
- `src/agents/orchestrator.py` - Added conditional edge and fallback support
- `TODO.md` - Added Phase 6 documentation

## Status

✅ **COMPLETED** - Revision loop mechanism fully implemented and integrated.
