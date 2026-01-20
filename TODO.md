# TODO.md - Deep Research Assistant Project

## 🔴 CRITICAL FIXES (Must Complete Before New Development)

**Status**: Blocking - These issues must be resolved first

### Priority 1: Security Fixes
- [ ] **Fix 1.1**: Remove hardcoded API key default from `config.py:13` - raise ConfigError if key is missing instead of using placeholder
- [ ] **Fix 1.2**: Create `.env.example` file with all required environment variables (DEEPSEEK_API_KEY, SEARCH_API_PROVIDER, TAVILY_API_KEY, etc.)

### Priority 2: Critical Logic Fixes
- [ ] **Fix 2.1**: Replace `asyncio.run()` in `src/main.py:94` with proper async Streamlit pattern (use `asyncio.create_task()` or Streamlit's async support)
- [ ] **Fix 2.2**: Fix streaming callback in `src/utils/streaming.py:88` - implement proper async-safe UI update mechanism
- [ ] **Fix 2.3**: Fix config provider logic in `src/utils/config.py:80-81` - correct conditional logic for provider selection
- [ ] **Fix 2.4**: Add missing `Source` import in `src/agents/orchestrator.py:265` - add `from ..models import Source`

### Priority 3: UX Improvements
- [ ] **Fix 3.1**: Implement proper loading states with progress indicators during async operations
- [ ] **Fix 3.2**: Add cancellation mechanism for ongoing research operations
- [ ] **Fix 3.3**: Review and improve error messages across all error paths
- [ ] **Fix 3.4**: Fix state management to prevent race conditions with concurrent queries

---

## Phase 1: Repository Initialization & Verification

Based on @Orchestrator_Tasks from PROJECT_CONTEXT.md

- [ ] **Task 1.1**: Verify comprehensive `.gitignore` file exists and covers Python, Streamlit, environment files, and data directories
- [ ] **Task 1.2**: Create `.env.example` template with placeholder variables for all API keys (DEEPSEEK_API_KEY, SEARCH_API_PROVIDER, TAVILY_API_KEY, etc.) - **Linked to Fix 1.2**
- [ ] **Task 1.3**: Verify repository structure matches PROJECT_CONTEXT.md requirements:
  - [ ] `src/` directory with `agents/`, `components/`, `utils/`, `main.py`
  - [ ] `tests/` directory
  - [ ] `docs/architecture/` directory
  - [ ] `data/raw/` and `data/reports/` directories
- [ ] **Task 1.4**: Verify `pyproject.toml` or `requirements.txt` includes all required dependencies (streamlit, langgraph, pydantic, python-dotenv, etc.)

---

## Phase 2: Architecture Design & Documentation

Based on @Orchestrator_Tasks from PROJECT_CONTEXT.md

### Task 2.1: Architecture Review & Specification Update

**Feature**: Complete Architecture Specification for Deep Research Assistant

**Status**: SPECS.md exists (901 lines) but needs verification and updates

**Breakdown for @ARCHITECT**:

#### Sub-task 2.1.1: Verify ResearchState Model Compliance
- [ ] **Verify** `ResearchState` Pydantic model in SPECS.md matches @Architect_Rules requirement for "Modular State"
- [ ] **Verify** model includes all required fields: query, sources, draft_report, status, query_id
- [ ] **Verify** model supports "Recursive Research" loop (iteration_count, max_iterations fields)
- [ ] **Verify** model is decoupled from UI rendering (pure data model)
- [ ] **Update** if missing: fields for tracking recursive research iterations and refinement

#### Sub-task 2.1.2: Verify Async Data Flow Architecture
- [ ] **Verify** SPECS.md Section 5 (Async Data Flow) properly defines Streamlit UI ↔ LangGraph backend communication
- [ ] **Verify** all external API calls (Search, LLM) are marked as async in API signatures
- [ ] **Verify** async patterns use `asyncio` and `st.rerun()` as required by @Architect_Rules
- [ ] **Verify** concurrent search operations use `asyncio.gather()` for parallel requests
- [ ] **Update** if missing: explicit documentation of how async prevents UI freezing

#### Sub-task 2.1.3: Verify Streaming Mechanism Specification
- [ ] **Verify** SPECS.md Section 5.2 (Streaming Mechanism) details how search results stream to UI in real-time
- [ ] **Verify** `StreamEvent` model is defined with proper event types (status, source, progress, report_chunk, error, complete)
- [ ] **Verify** streaming callback mechanism is async-safe and doesn't block UI
- [ ] **Verify** streaming includes proper rate limiting to prevent UI flooding
- [ ] **Update** if missing: specific implementation details for async-safe UI updates without blocking

#### Sub-task 2.1.4: Verify Agent Architecture
- [ ] **Verify** SPECS.md defines Research Agent, Reviewer Agent, and Writer Agent
- [ ] **Verify** each agent has clear responsibilities and input/output contracts
- [ ] **Verify** LangGraph workflow orchestration is specified (nodes, edges, conditional logic)
- [ ] **Verify** "Recursive Research" loop is defined (how agents iterate and refine results)
- [ ] **Update** if missing: recursive iteration logic and stopping conditions

#### Sub-task 2.1.5: Verify Error Handling & State Management
- [ ] **Verify** SPECS.md Section 8 (Error Handling Patterns) addresses @Coder_Standards requirement
- [ ] **Verify** error handling includes user-friendly messages for Streamlit frontend
- [ ] **Verify** state management prevents race conditions with concurrent queries
- [ ] **Verify** error recovery strategies are defined (retry logic, fallbacks, partial failures)
- [ ] **Update** if missing: specific error message templates and state isolation patterns

#### Sub-task 2.1.6: Verify Secret Isolation Compliance
- [ ] **Verify** SPECS.md Section 3.3.1 (Config Management) enforces @Architect_Rules requirement
- [ ] **Verify** configuration loading prioritizes `st.secrets` (cloud) then `python-dotenv` (local)
- [ ] **Verify** no hardcoded API keys are allowed in specification
- [ ] **Verify** ConfigError is raised if required keys are missing (no placeholders)
- [ ] **Update** if missing: explicit prohibition of hardcoded credentials

#### Sub-task 2.1.7: Verify Recursive Research Loop Specification
- [ ] **Verify** SPECS.md addresses PROJECT_CONTEXT.md goal: "Recursive Research loop"
- [ ] **Verify** workflow supports iterative refinement (user asks question → research → review → write → potential refinement)
- [ ] **Verify** stopping conditions for recursion are defined (max_iterations, confidence thresholds)
- [ ] **Update** if missing: explicit recursive research workflow diagram and logic

#### Sub-task 2.1.8: Create Architecture Documentation Summary
- [ ] **Create** `docs/architecture/ARCHITECTURE_OVERVIEW.md` summarizing key architectural decisions
- [ ] **Create** `docs/architecture/DATA_FLOW.md` with detailed data flow diagrams
- [ ] **Create** `docs/architecture/AGENT_WORKFLOW.md` documenting the recursive research process
- [ ] **Update** SPECS.md with cross-references to architecture documentation

#### Sub-task 2.1.9: Final Architecture Review
- [ ] **Review** entire SPECS.md for consistency and completeness
- [ ] **Verify** all @Architect_Rules are addressed
- [ ] **Verify** all @Orchestrator_Tasks requirements are met
- [ ] **Mark** Task 2.1 complete when all sub-tasks are verified/updated

---

## Phase 3: Skeleton Implementation Verification

Based on @Orchestrator_Tasks from PROJECT_CONTEXT.md

- [ ] **Task 3.1**: Verify `src/main.py` has basic Streamlit app structure
- [ ] **Task 3.2**: Verify environment variable loading uses `python-dotenv` with proper fallback error handling (no hardcoded defaults)
- [ ] **Task 3.3**: Verify basic chat interface UI exists in Streamlit (input box, message display area)
- [ ] **Task 3.4**: Verify async search integration is properly implemented (not blocking)
- [ ] **Task 3.5**: Test "Hello World" app runs successfully and displays chat interface without freezing

---

## Phase 4: Core Agent Implementation (Future)

- [ ] **Task 4.1**: Verify Research Agent has async web search capabilities
- [ ] **Task 4.2**: Verify Reviewer Agent implements fact-checking and verification
- [ ] **Task 4.3**: Verify Writer Agent generates reports with citations
- [ ] **Task 4.4**: Verify LangGraph workflow orchestration is properly integrated
- [ ] **Task 4.5**: Verify streaming results to Streamlit UI works in real-time

---

## Phase 5: Testing & Documentation (Future)

- [ ] **Task 5.1**: Write comprehensive unit tests for core components
- [ ] **Task 5.2**: Update README.md with setup instructions matching PROJECT_CONTEXT.md structure
- [ ] **Task 5.3**: Document API usage and configuration in `docs/architecture/`

---

## Phase 6: Revision Loop Implementation ✅ COMPLETED

**Feature**: Recursive Research Loop with Quality-Based Revision

**Status**: ✅ Implemented - Reviewer agent can trigger revision loop back to research

### Task 6.1: Revision Loop Mechanism ✅
- [x] **Task 6.1.1**: Add `NEEDS_REVISION` status to `ResearchStatus` enum in `src/models.py`
- [x] **Task 6.1.2**: Update `review_node` in `src/agents/reviewer_agent.py` to check quality threshold
- [x] **Task 6.1.3**: Implement quality check logic (minimum 2 verified sources required)
- [x] **Task 6.1.4**: Return `needs_revision` status with proper state update when quality is insufficient
- [x] **Task 6.1.5**: Increment `iteration_count` to prevent infinite loops
- [x] **Task 6.1.6**: Clear bad sources and search queries when triggering revision

### Task 6.2: Orchestrator Integration ✅
- [x] **Task 6.2.1**: Update `_review_decision` function in `src/agents/orchestrator.py` to handle `needs_revision`
- [x] **Task 6.2.2**: Add conditional edge from review → research for revision loop
- [x] **Task 6.2.3**: Implement max iterations check to prevent infinite loops
- [x] **Task 6.2.4**: Update fallback mode to support revision loop (non-LangGraph execution)

### Task 6.3: State Management ✅
- [x] **Task 6.3.1**: Ensure `iteration_count` is properly tracked across revisions
- [x] **Task 6.3.2**: Clear sources and search_queries when revision is triggered
- [x] **Task 6.3.3**: Preserve query and query_id during revision loop
- [x] **Task 6.3.4**: Set `error_message` with feedback for next research iteration

### Implementation Details:
- **Quality Threshold**: Minimum 2 verified sources required
- **Max Iterations**: Default 5 (configurable via `max_iterations`)
- **State Update on Revision**:
  ```python
  {
      "status": "needs_revision",
      "iteration_count": state.get("iteration_count", 0) + 1,
      "error_message": "Insufficient verified sources (found 0/2). Try broader search terms.",
      "sources": [],
      "search_queries": [],
      "current_agent": "reviewer"
  }
  ```
- **Loop Behavior**: Review → Research (if needs_revision) → Review → Write (if quality passes)

### Next Steps:
- [ ] **Task 6.4**: Test revision loop with various scenarios (insufficient sources, max iterations)
- [ ] **Task 6.5**: Enhance error_message to provide more specific feedback to research agent
- [ ] **Task 6.6**: Consider making quality threshold configurable via Config
- [ ] **Task 6.7**: Add logging/metrics for revision loop frequency

---

## Phase 7: True Agentic Intelligence Implementation ✅ COMPLETED

**Feature**: Stop "Blind Retries" and Add LLM-Based Verification

**Status**: ✅ Implemented - Agents now learn from feedback and use LLM for intelligent verification

### Task 7.1: Fix Research Agent - Stop Blind Retries ✅
- [x] **Task 7.1.1**: Update `generate_search_queries` to accept `context` as `str` (error message) instead of `List[str]`
- [x] **Task 7.1.2**: Update prompt to use error message context and instruct LLM to generate DIFFERENT queries on revision
- [x] **Task 7.1.3**: Implement LLM-based query generation with proper parsing
- [x] **Task 7.1.4**: Update `research_node` to capture `error_message` from state
- [x] **Task 7.1.5**: Pass `error_message` as context to `generate_search_queries`
- [x] **Task 7.1.6**: Load LLM client in `research_node` for intelligent query generation

### Task 7.2: Fix Reviewer Agent - Add LLM Brain ✅
- [x] **Task 7.2.1**: Update `verify_source` to use LLM for intelligent verification instead of just math checks
- [x] **Task 7.2.2**: Increase snippet threshold from 20 to 50 characters (hard filter)
- [x] **Task 7.2.3**: Implement LLM prompt to check if snippet contains specific facts/data vs generic SEO spam
- [x] **Task 7.2.4**: Add fallback to relevance score if LLM verification fails
- [x] **Task 7.2.5**: Update `review_node` to load and pass LLM client to `verify_source`
- [x] **Task 7.2.6**: Ensure async LLM calls use `ainvoke` for proper async handling

### Implementation Details:

#### Research Agent Improvements:
- **Context Type**: Changed from `Optional[List[str]]` to `Optional[str]` to accept error messages
- **Prompt Engineering**: 
  ```
  "If the context mentions 'Insufficient sources', you MUST generate DIFFERENT queries than before.
   Try broader terms, synonyms, or break the topic into smaller sub-questions."
  ```
- **LLM Integration**: Uses `create_llm_client()` to get OpenAI client
- **Error Message Flow**: `error_message` from reviewer → passed as `context` to query generator

#### Reviewer Agent Improvements:
- **Hard Filter**: Snippet must be ≥50 characters (increased from 20)
- **LLM Verification**: 
  ```
  "Return YES only if the text contains specific facts/data. Return NO if it is generic SEO spam."
  ```
- **Intelligent Check**: No longer trusts search engine relevance scores blindly
- **Fallback**: Uses relevance score > 0.4 if LLM unavailable or fails

### Key Changes:

**Before (Blind Retries)**:
- Research agent ignored error messages
- Generated same queries on each iteration
- Reviewer trusted search engine scores

**After (True Agentic)**:
- Research agent reads error messages and adapts
- Generates different queries based on feedback
- Reviewer uses LLM to verify actual content quality

### Files Modified:
- `src/agents/research_agent.py` - Updated query generation and research_node
- `src/agents/reviewer_agent.py` - Added LLM-based verification

### Next Steps:
- [ ] **Task 7.3**: Test with queries that trigger revision loop to verify different queries are generated
- [ ] **Task 7.4**: Test LLM verification with various source types (good sources, spam, low-quality)
- [ ] **Task 7.5**: Monitor API usage/costs for LLM calls in query generation and verification
- [ ] **Task 7.6**: Add caching for LLM verification results to reduce API calls
- [ ] **Task 7.7**: Consider batch verification of sources for efficiency

---

## Phase 8: Phase 7 Feature Audit - Refactoring & Optimization

**Feature**: Performance Optimization, Caching, and Enhanced Intelligence

**Status**: 🔄 **PENDING** - Follow-up tasks from Phase 7 Feature Audit (SPECS.md Sections 12.8 & 13.7)

**Source**: Based on refactoring recommendations from Phase 7 implementation audit

### Task 8.1: High Priority Performance Optimizations

#### Task 8.1.1: Batch Source Verification
- [ ] **Current Issue**: Verifies sources one-by-one, causing N LLM API calls for N sources
- [ ] **Solution**: Batch multiple sources in single LLM call
- [ ] **Impact**: Reduces API calls and latency significantly
- [ ] **File**: `src/agents/reviewer_agent.py`
- [ ] **Implementation**: Create `verify_sources_batch()` function that takes multiple sources and returns batch verification results

#### Task 8.1.2: Cache LLM Verification Results
- [ ] **Current Issue**: Verifies same source multiple times if revision occurs
- [ ] **Solution**: Cache verification results by URL hash
- [ ] **Impact**: Reduces redundant API calls
- [ ] **Files**: 
  - [ ] Create `src/utils/cache.py` for caching utilities
  - [ ] Update `src/agents/reviewer_agent.py` to use cache
- [ ] **Implementation**: 
  - [ ] Create cache key from URL hash
  - [ ] Store verification results (is_verified, confidence_score)
  - [ ] Check cache before LLM call
  - [ ] TTL: 24 hours (sources may change)

#### Task 8.1.3: Monitor API Usage & Costs
- [ ] **Current Issue**: No tracking of LLM API usage/costs
- [ ] **Solution**: Add metrics for LLM calls per query
- [ ] **Impact**: Better cost visibility and optimization
- [ ] **Files**:
  - [ ] Create `src/utils/metrics.py` for metrics tracking
  - [ ] Update `src/utils/logger.py` to include metrics
  - [ ] Update `src/agents/research_agent.py` to track query generation calls
  - [ ] Update `src/agents/reviewer_agent.py` to track verification calls
- [ ] **Implementation**:
  - [ ] Track: number of LLM calls, tokens used, cost estimate
  - [ ] Log metrics per query_id
  - [ ] Add summary metrics to final state

#### Task 8.1.4: Make Quality Threshold Configurable
- [ ] **Current Issue**: Hardcoded `min_verified_sources = 2` in `review_node`
- [ ] **Solution**: Add to `Config` class and load from environment
- [ ] **Impact**: Allows users to adjust quality requirements
- [ ] **Files**: 
  - [ ] Update `src/utils/config.py` to add `MIN_VERIFIED_SOURCES` setting
  - [ ] Update `src/agents/reviewer_agent.py:177` to use config value
- [ ] **Implementation**:
  - [ ] Add `MIN_VERIFIED_SOURCES: int = 2` to Config class
  - [ ] Load from environment variable `MIN_VERIFIED_SOURCES`
  - [ ] Update review_node to use `config.MIN_VERIFIED_SOURCES`

#### Task 8.1.5: Enhance Error Messages for Research Agent
- [ ] **Current Issue**: Generic message "Try broader search terms"
- [ ] **Solution**: More specific feedback based on failure reason
- [ ] **Impact**: Better query refinement in next iteration
- [ ] **File**: `src/agents/reviewer_agent.py:193`
- [ ] **Implementation**:
  - [ ] Analyze why sources failed (snippet too short, LLM rejected, etc.)
  - [ ] Generate specific feedback: "Try synonyms for X", "Break into sub-questions", "Use more specific terms"
  - [ ] Use LLM to generate better error messages if needed

#### Task 8.1.6: Add Revision Loop Metrics
- [ ] **Current Issue**: No logging/metrics for revision frequency
- [ ] **Solution**: Track revision triggers, success rate, iteration patterns
- [ ] **Impact**: Better observability and debugging
- [ ] **Files**: 
  - [ ] Update `src/agents/reviewer_agent.py` to log revision events
  - [ ] Update `src/utils/logger.py` to support metrics
- [ ] **Implementation**:
  - [ ] Log: revision trigger reason, iteration count, sources found
  - [ ] Track: revision frequency per query type
  - [ ] Add metrics to final state for analysis

### Task 8.2: Medium Priority Enhancements

#### Task 8.2.1: Improve Error Message Specificity
- [ ] **Current Issue**: Generic "Try broader search terms"
- [ ] **Solution**: More specific feedback (e.g., "Try synonyms for X", "Break into sub-questions")
- [ ] **Impact**: Better query refinement
- [ ] **File**: `src/agents/reviewer_agent.py:193`
- [ ] **Implementation**: Use LLM to analyze failure and generate specific suggestions

#### Task 8.2.2: Adaptive Snippet Threshold
- [ ] **Current Issue**: Fixed 50 character threshold
- [ ] **Solution**: Adjust based on query complexity or domain
- [ ] **Impact**: More flexible filtering
- [ ] **File**: `src/agents/reviewer_agent.py:32`
- [ ] **Implementation**: 
  - [ ] Analyze query complexity
  - [ ] Adjust threshold dynamically (e.g., 30 for simple queries, 70 for complex)

#### Task 8.2.3: Query Generation Caching
- [ ] **Current Issue**: Generates queries fresh each time
- [ ] **Solution**: Cache query generation for same query+context
- [ ] **Impact**: Reduces redundant LLM calls
- [ ] **File**: `src/agents/research_agent.py`
- [ ] **Implementation**:
  - [ ] Create cache key from (query, context) hash
  - [ ] Check cache before LLM call
  - [ ] TTL: 1 hour (queries may need refresh)

#### Task 8.2.4: Query Refinement Based on Error Message
- [ ] **Current Issue**: Research agent doesn't explicitly analyze `error_message` for refinement
- [ ] **Solution**: Research agent should analyze `error_message` to improve queries
- [ ] **Impact**: Better query generation in revision iterations
- [ ] **File**: `src/agents/research_agent.py`
- [ ] **Implementation**: 
  - [ ] Parse error_message for specific suggestions
  - [ ] Use suggestions in prompt to LLM
  - [ ] Generate queries that address specific failure reasons

### Task 8.3: Testing Requirements

#### Task 8.3.1: Query Generation Tests
- [ ] **Test 8.3.1.1**: Error Message Context Test
  - [ ] Input: Query with error_message "Insufficient sources"
  - [ ] Expected: LLM generates DIFFERENT queries than first attempt
  - [ ] Verify: Queries are broader/different from original
- [ ] **Test 8.3.1.2**: Fallback Test
  - [ ] Input: LLM unavailable
  - [ ] Expected: Falls back to simple query variations
  - [ ] Verify: System still functions without LLM
- [ ] **Test 8.3.1.3**: Query Parsing Test
  - [ ] Input: LLM returns numbered list or bullet points
  - [ ] Expected: Properly parses queries from various formats
  - [ ] Verify: All queries extracted correctly

#### Task 8.3.2: Source Verification Tests
- [ ] **Test 8.3.2.1**: LLM Verification Test
  - [ ] Input: Source with specific facts vs generic SEO spam
  - [ ] Expected: LLM correctly identifies quality sources
  - [ ] Verify: High-quality sources pass, spam rejected
- [ ] **Test 8.3.2.2**: Hard Filter Test
  - [ ] Input: Source with snippet < 50 characters
  - [ ] Expected: Rejected before LLM call
  - [ ] Verify: No unnecessary LLM calls
- [ ] **Test 8.3.2.3**: Fallback Test
  - [ ] Input: LLM unavailable or fails
  - [ ] Expected: Falls back to relevance score check
  - [ ] Verify: System still functions without LLM
- [ ] **Test 8.3.2.4**: Async Handling Test
  - [ ] Input: Multiple sources to verify
  - [ ] Expected: All verifications complete without blocking
  - [ ] Verify: Proper async execution

#### Task 8.3.3: Batch Verification Tests
- [ ] **Test 8.3.3.1**: Batch Verification Test
  - [ ] Input: 10 sources to verify
  - [ ] Expected: Single LLM call processes all sources
  - [ ] Verify: All sources verified correctly, reduced API calls
- [ ] **Test 8.3.3.2**: Cache Hit Test
  - [ ] Input: Same source verified twice
  - [ ] Expected: Second verification uses cache
  - [ ] Verify: No redundant LLM call

### Task 8.4: Documentation Updates

- [ ] **Task 8.4.1**: Document caching strategy in `docs/architecture/`
- [ ] **Task 8.4.2**: Document metrics and monitoring in `docs/architecture/`
- [ ] **Task 8.4.3**: Update `SPECS.md` with implemented optimizations
- [ ] **Task 8.4.4**: Create performance benchmarks document

### Implementation Priority

**Phase 8.1 (High Priority)** - Should be implemented first:
1. Batch source verification (biggest API cost savings)
2. Cache LLM verification results (reduces redundant calls)
3. Monitor API usage (visibility before optimization)
4. Configurable quality threshold (user flexibility)
5. Enhanced error messages (better agentic behavior)
6. Revision loop metrics (observability)

**Phase 8.2 (Medium Priority)** - Can be implemented after Phase 8.1:
- Error message specificity improvements
- Adaptive thresholds
- Query generation caching
- Query refinement enhancements

**Phase 8.3 (Testing)** - Should be done in parallel with implementation:
- All tests should be written as features are implemented

---

---

## Current Status & Next Steps

**Current Phase**: Phase 2 - Architecture Design & Documentation

**Current Status**: 
- 🔴 Critical Fixes (Priority 1 & 2) - **BLOCKING** - Must be completed first
- 🟡 Phase 2 Task 2.1 - **READY FOR ARCHITECT** - Architecture specification review and update

**Next Agent**: @ARCHITECT

**Architect Assignment**: 
Complete **Task 2.1: Architecture Review & Specification Update** (9 sub-tasks detailed above)

**Architect Instructions**:
1. Read `docs/PROJECT_CONTEXT.md` to understand project goals and rules
2. Review existing `SPECS.md` (901 lines) against requirements
3. Complete all 9 sub-tasks in Task 2.1 to verify/update architecture specification
4. Ensure SPECS.md fully addresses:
   - @Architect_Rules (Async/Await, Secret Isolation, Modular State)
   - @Orchestrator_Tasks requirement for async streaming
   - "Recursive Research" loop from project goal
   - All error handling and state management patterns
5. Create architecture documentation in `docs/architecture/` if needed
6. Mark Task 2.1 complete when specification is verified and updated

**Note**: While critical fixes are blocking new development, the Architect can proceed with specification review and updates in parallel, as this is documentation work that doesn't require code changes.
