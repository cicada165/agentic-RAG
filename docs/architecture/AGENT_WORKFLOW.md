# Agent Workflow - Deep Research Assistant

## Recursive Research Loop

The system implements a **Quality-Based Revision Loop** where the Reviewer agent evaluates research quality and triggers automatic revision if quality thresholds are not met.

### Workflow
1. **Research**: Generate queries and collect sources.
2. **Review**: Verify sources and detect conflicts.
3. **Quality Check**:
   - If `verified_sources < MIN_VERIFIED_SOURCES` and `iterations < MAX_ITERATIONS`:
     - Set status to `NEEDS_REVISION`.
     - Clear sources/queries.
     - Loop back to **Research**.
   - Else: Proceed to **Write**.
4. **Write**: Generate final report.

### Agentic Intelligence (Phase 7)
- **Learned Feedback**: The Research Agent uses the `error_message` from the Reviewer (e.g., "Insufficient sources") to generate *different* and broader queries in the next iteration.
- **LLM Verification**: The Reviewer uses LLM-based analysis to distinguish between factual data and SEO spam, instead of relying solely on search engine relevance scores.
