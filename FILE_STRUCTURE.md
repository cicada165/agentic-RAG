# Project File Structure

## 📁 Complete File List

```
agentic-RAG/
│
├── 📄 Configuration & Setup Files
│   ├── .cursorrules                    # Cursor IDE rules
│   ├── .env.example                    # Environment variables template
│   ├── .gitignore                      # Git ignore rules
│   ├── pytest.ini                      # Pytest configuration
│   ├── requirements.txt                # Python dependencies
│   └── config.py                       # Legacy config (for old RAG system)
│
├── 📄 Documentation Files
│   ├── README.md                       # Main project README
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── QUICK_SETUP.md                  # Quick setup guide
│   ├── QUICK_COMMANDS.md               # Command reference
│   ├── TESTING_GUIDE.md                # Testing documentation
│   ├── OPENAI_MIGRATION_SUMMARY.md     # OpenAI migration notes
│   ├── TODO.md                         # Project TODO list
│   ├── SPECS.md                        # Technical specifications (1403 lines)
│   └── FILE_STRUCTURE.md               # This file
│
├── 📄 Entry Points & Main Scripts
│   ├── main.py                         # Legacy CLI entry point (old RAG system)
│   ├── streamlit_app.py                # Streamlit app entry point
│   ├── test_setup.py                   # Comprehensive test script
│   └── example_usage.py                # Usage examples
│
├── 📄 Legacy RAG System Files
│   ├── agentic_rag.py                  # Legacy agentic RAG agent
│   ├── agent_tools.py                  # Legacy agent tools
│   └── offline_pipeline.py             # Legacy offline pipeline
│
├── 📁 src/                             # Main source code directory
│   ├── __init__.py
│   ├── main.py                         # Streamlit main application
│   ├── models.py                       # Pydantic data models
│   │
│   ├── 📁 agents/                      # Agent implementations
│   │   ├── __init__.py
│   │   ├── orchestrator.py             # LangGraph workflow orchestration
│   │   ├── research_agent.py           # Research agent (web search)
│   │   ├── reviewer_agent.py           # Reviewer agent (fact-checking)
│   │   └── writer_agent.py             # Writer agent (report generation)
│   │
│   ├── 📁 components/                  # Streamlit UI components
│   │   ├── __init__.py
│   │   └── chat_interface.py          # Chat UI components
│   │
│   └── 📁 utils/                       # Utility modules
│       ├── __init__.py
│       ├── config.py                   # Configuration management (OpenAI)
│       ├── exceptions.py               # Custom exceptions
│       ├── llm_client.py              # OpenAI LLM client utility
│       ├── logger.py                   # Logging setup
│       ├── state_manager.py            # Streamlit state management
│       └── streaming.py                # Streaming utilities
│
├── 📁 docs/                            # Documentation directory
│   ├── PROJECT_CONTEXT.md              # Project context and goals
│   └── SETUP_REQUIREMENTS.md           # Setup requirements guide
│
├── 📁 documents/                       # Sample documents
│   └── sample_document.txt            # Sample document for testing
│
└── 📁 tests/                           # Test files
    ├── __init__.py
    ├── test_config.py                  # Configuration tests
    ├── test_models.py                  # Data model tests
    └── test_research_agent.py          # Research agent tests
```

## 📊 File Count Summary

### By Category:
- **Configuration Files**: 6 files
- **Documentation Files**: 9 files
- **Entry Points**: 4 files
- **Legacy RAG Files**: 3 files
- **Source Code (src/)**: 15 files
  - Agents: 4 files
  - Components: 2 files
  - Utils: 7 files
  - Main: 2 files
- **Tests**: 4 files
- **Total**: ~45 files (excluding __pycache__ and generated files)

## 🗂️ Key Directories

### `src/` - Main Application Code
- **`agents/`**: Core agent logic (Research, Reviewer, Writer)
- **`components/`**: Streamlit UI components
- **`utils/`**: Helper functions and utilities

### `docs/` - Documentation
- Project context and setup guides

### `tests/` - Test Suite
- Unit tests for configuration, models, and agents

### Root Level
- Entry points (`streamlit_app.py`, `main.py`)
- Configuration (`config.py`, `requirements.txt`)
- Documentation (multiple `.md` files)

## 🔍 Important Files

### Entry Points:
- **`streamlit_app.py`** - Main Streamlit app entry point
- **`src/main.py`** - Streamlit application logic
- **`main.py`** - Legacy CLI entry point

### Configuration:
- **`src/utils/config.py`** - OpenAI configuration (NEW)
- **`config.py`** - Legacy DeepSeek config (OLD)

### Core Logic:
- **`src/agents/orchestrator.py`** - Workflow orchestration
- **`src/models.py`** - Data models (ResearchState, Source, etc.)

### Testing:
- **`test_setup.py`** - Comprehensive test script
- **`tests/`** - Unit test files

## 📝 Notes

- **Legacy Files**: `agentic_rag.py`, `agent_tools.py`, `offline_pipeline.py` are from the old RAG system and may not be used by the new Streamlit app
- **Cache Directories**: `__pycache__/` directories are generated and ignored by git
- **Generated Files**: `.pytest_cache/`, `rag_cache/` are generated during runtime
