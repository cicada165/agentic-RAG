# PROJECT_CONTEXT.md


agentic-rag/
├── .github/workflows/    # CI/CD pipelines
├── data/
│   ├── raw/              # Temporary search dumps
│   └── reports/          # Final markdown outputs
├── docs/
│   ├── PROJECT_CONTEXT.md
│   └── architecture/
├── src/
│   ├── agents/           # Core logic (Research, Reviewer, Writer)
│   ├── components/       # Streamlit UI widgets
│   ├── utils/            # Helper functions (logging, config)
│   └── main.py           # App entry point
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml        # Poetry/Pip dependency management
└── README.md

## @Project_Goal
We are building a "Deep Research Assistant" dashboard using Streamlit that automates the process of gathering, synthesizing, and verifying complex information from the web. The goal is to provide a "Recursive Research" loop where users can ask a broad question (e.g., "State of EV batteries in 2026") and receive a fully cited, fact-checked report in Markdown format, bypassing the need for manual Google searching.

## @Orchestrator_Tasks
1.  **Repo Initialization**: Initialize the `deep-research-assistant` repository with the standard `src/`, `tests/`, and `docs/` structure, including a comprehensive `.gitignore` and `.env.example` to prevent secret leaks.
2.  **Architecture Setup**: Create the `SPECS.md` file to define the data flow between the Streamlit frontend (UI) and the LangGraph backend (Agent Logic), specifically detailing how asynchronous search results will stream to the UI.
3.  **Skeleton Implementation**: Create a "Hello World" Streamlit app in `src/main.py` that successfully loads environment variables and displays a basic chat interface, verifying the development environment is ready.

## @Architect_Rules
1.  **Async/Await**: All external API calls (Search, LLM) must be asynchronous to prevent freezing the Streamlit UI. Use `asyncio` and `st.rerun()` patterns where appropriate.
2.  **Secret Isolation**: STRICTLY forbid hardcoding API keys. All credentials must be loaded via `st.secrets` (for cloud) or `python-dotenv` (for local), with a fallback error message if missing.
3.  **Modular State**: The application state must be decoupled from the UI rendering. Use a `ResearchState` Pydantic model to track the progress of queries, sources, and draft reports.

## @Coder_Standards
1.  **Type Safety**: All function signatures must use Python type hints (e.g., `def fetch_results(query: str) -> list[SearchResult]:`).
2.  **Docstrings**: Use Google-style docstrings for every class and complex function, specifically explaining the `Args` and `Returns`.
3.  **Error Handling**: No silent failures. Wrap external calls in `try/except` blocks and bubble up user-friendly error messages to the Streamlit frontend (e.g., "Search API timed out, retrying...").