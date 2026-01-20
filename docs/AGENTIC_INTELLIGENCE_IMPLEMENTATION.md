# True Agentic Intelligence Implementation

## Overview

This phase implements true "agentic" behavior by:
1. **Stopping Blind Retries**: Research agent now learns from feedback and generates different queries
2. **Adding LLM Brain**: Reviewer agent uses LLM to verify sources instead of blindly trusting search engine scores

## Problem Statement

### Before (Blind Retries)
- Research agent ignored error messages from reviewer
- Generated the exact same queries on each revision loop
- Reviewer trusted search engine relevance scores without verification
- Low-quality sources could pass verification if search engine gave high scores

### After (True Agentic)
- Research agent reads error messages and adapts query strategy
- Generates different queries based on feedback (broader terms, synonyms, sub-questions)
- Reviewer uses LLM to verify actual content quality
- Only sources with real facts/data pass verification

## Implementation Details

### 1. Research Agent - Stop Blind Retries

#### Changes to `generate_search_queries`:

**Before**:
```python
async def generate_search_queries(
    query: str,
    context: Optional[List[str]] = None,  # List of previous searches
    ...
)
```

**After**:
```python
async def generate_search_queries(
    query: str,
    context: Optional[str] = None,  # Error message from reviewer
    ...
)
```

**Updated Prompt**:
```
Task: Generate {max_queries} Google search queries for the topic: "{query}"

Context from previous attempt: {context if context else "First attempt"}

CRITICAL INSTRUCTION:
If the context mentions "Insufficient sources", you MUST generate DIFFERENT queries than before. 
Try broader terms, synonyms, or break the topic into smaller sub-questions.
```

#### Changes to `research_node`:

**Key Addition**:
```python
# CAPTURE THE FEEDBACK from previous attempt
previous_error = state.get("error_message")

# PASS FEEDBACK TO BRAIN - The Agent now "hears" the complaint
search_queries = await generate_search_queries(
    query,
    context=previous_error,  # Pass error message as context
    max_queries=5,
    llm_client=llm_client
)
```

### 2. Reviewer Agent - Add LLM Brain

#### Changes to `verify_source`:

**Before** (Math-based):
```python
if source.relevance_score < 0.3:
    return False, 0.2
# Just trusted search engine scores
```

**After** (LLM-based):
```python
# 1. HARD FILTER: Garbage Snippets
if not source.snippet or len(source.snippet) < 50:  # Increased threshold
    return False, 0.0

# 2. INTELLIGENT FILTER: Ask the LLM
prompt = f"""Verify if this text answers the query: "{query}"
Text: "{source.snippet}"

Return YES only if the text contains specific facts/data. Return NO if it is generic SEO spam."""

response = await llm_client.ainvoke(prompt)
is_valid = "YES" in response.content.upper()
return is_valid, 0.9 if is_valid else 0.1
```

#### Changes to `review_node`:

**Key Addition**:
```python
# Load LLM client for intelligent verification
from ..utils.llm_client import create_llm_client
llm_client = create_llm_client()

# Verify each source with LLM
for source in sources:
    is_verified, confidence = await verify_source(source, query, llm_client=llm_client)
```

## Workflow Example

### Scenario: Insufficient Sources Found

1. **First Attempt**:
   - Research: Generates queries ["AI trends 2024", "machine learning news"]
   - Review: Finds 0 verified sources (all failed LLM verification)
   - Returns: `needs_revision` with error_message

2. **Second Attempt** (Now Agentic):
   - Research: Reads error_message "Insufficient verified sources (found 0/2). Try broader search terms."
   - LLM generates NEW queries: ["artificial intelligence developments", "AI industry updates", "machine learning advancements 2024"]
   - Review: Finds 2+ verified sources (LLM verified they contain real facts)
   - Proceeds to write phase

## Key Improvements

### 1. Adaptive Query Generation
- **Before**: Same queries every time
- **After**: Different queries based on feedback
- **Benefit**: Higher chance of finding quality sources

### 2. Intelligent Source Verification
- **Before**: Trusted search engine scores (could be manipulated)
- **After**: LLM verifies actual content quality
- **Benefit**: Filters out SEO spam and low-quality content

### 3. Feedback Loop
- **Before**: No learning from failures
- **After**: Error messages guide next attempt
- **Benefit**: True recursive improvement

## Configuration

- **Snippet Threshold**: 50 characters (hard filter)
- **LLM Verification**: Uses OpenAI (gpt-4o-mini by default)
- **Fallback**: Uses relevance score if LLM unavailable

## Safety & Fallbacks

1. **LLM Unavailable**: Falls back to relevance score checks
2. **LLM Failure**: Catches exceptions and uses fallback
3. **Query Parsing**: Handles various LLM response formats
4. **Error Handling**: Logs warnings but continues execution

## Performance Considerations

- **API Costs**: Each revision loop uses LLM for:
  - Query generation (1 call)
  - Source verification (N calls, where N = number of sources)
- **Optimization Opportunities**:
  - Cache verification results
  - Batch verify sources
  - Use cheaper model for verification

## Testing Scenarios

1. **Revision Loop with Learning**:
   - Query that initially fails
   - Verify different queries generated on second attempt
   - Verify sources pass LLM verification

2. **LLM Verification**:
   - Test with high-quality sources (should pass)
   - Test with SEO spam (should fail)
   - Test with low-quality snippets (should fail)

3. **Fallback Behavior**:
   - Test when LLM unavailable
   - Verify fallback to relevance scores works

## Files Modified

- `src/agents/research_agent.py`:
  - Updated `generate_search_queries` signature and prompt
  - Updated `research_node` to pass error_message
  
- `src/agents/reviewer_agent.py`:
  - Updated `verify_source` to use LLM
  - Updated `review_node` to load LLM client

- `TODO.md`:
  - Added Phase 7 documentation

## Status

✅ **COMPLETED** - True agentic intelligence fully implemented.

The system now:
- Learns from feedback
- Adapts query strategy
- Verifies sources intelligently
- Implements true recursive improvement
