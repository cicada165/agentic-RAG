# SPECS.md - Deep Research Assistant Technical Specifications

This document serves as a summary of the technical specifications for the Deep Research Assistant. For detailed information, please refer to the specific documentation files in `docs/architecture/`.

## Architectural Documentation

- **[Architecture Overview](docs/architecture/ARCHITECTURE_OVERVIEW.md)**: High-level design and technology stack.
- **[Data Flow & State](docs/architecture/DATA_FLOW.md)**: Async communication and state management.
- **[Agent Workflow](docs/architecture/AGENT_WORKFLOW.md)**: Recursive research loops and agentic intelligence.
- **[API Signatures](docs/architecture/API_SIGNATURES.md)**: Detailed node functions and interfaces.

## Key Features

1.  **Modular Agent Architecture**: Independent Research, Reviewer, and Writer agents orchestrated by LangGraph.
2.  **Recursive Research Loop**: Quality-based revision system that automatically refines research until thresholds are met.
3.  **Agentic Intelligence**: Researchers that learn from negative feedback (e.g., "Insufficient sources") to adapt their search strategy.
4.  **Async Streaming**: Real-time status and source updates in the Streamlit UI without blocking.
5.  **Cost & Usage Monitoring**: Real-time tracking of token usage and estimated costs for LLM operations.