# Agentic RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system with agentic capabilities, allowing the LLM to autonomously decide when and how to use retrieval tools to answer user queries.

## Features

### 🎯 Core Capabilities

- **Intelligent Query Processing**: Automatically rewrites unclear queries and extracts keywords
- **Hybrid Retrieval**: Combines vector similarity search with keyword-based re-ranking
- **Document Refinement**: Filters and summarizes retrieved documents for better context
- **Agentic Decision Making**: LLM autonomously decides when to use RAG vs. direct answers
- **Batch Verification**: Optimized source fact-checking using LLM batch processing
- **Intelligent Caching**: Caches verification results to reduce API costs and latency
- **API Usage Monitoring**: Real-time tracking of token usage and estimated costs
- **Iterative Refinement**: Automatically retries with rewritten queries if initial retrieval fails

### 🔧 Key Components

1. **Offline Pipeline**: Document loading, chunking, BM25 encoding, vectorization, and storage
2. **Agent Tools**: Query rewriting, retrieval augmentation, and document summarization
3. **Agentic Agent**: Orchestrates tool usage based on query analysis
4. **Vector Database**: Chroma for efficient similarity search
5. **BM25 Model**: Keyword-based retrieval for hybrid search

## Installation

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (optional, for faster embeddings)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-RAG
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API key:
   - Set `DEEPSEEK_API_KEY` in `config.py` or as an environment variable
   - Or update `config.py` directly with your API key

4. (Optional) For Chinese text processing, jieba is included. For other languages, you may need to adjust the tokenization in `offline_pipeline.py`.

## Quick Start

### 1. Build the Knowledge Base

First, prepare your documents and build the knowledge base:

```bash
python main.py --build --document ./documents/sample_document.txt
```

Or use the default document path:
```bash
python main.py --build
```

This will:
- Load and chunk your documents
- Create BM25 model for keyword search
- Generate embeddings and store in Chroma vector database
- Save everything to `./rag_cache/`

### 2. Query the System

#### Interactive Mode (Recommended)
```bash
python main.py --interactive
```

#### Single Query
```bash
python main.py --query "什么情况会被退学?"
```

#### Python API
```python
from agentic_rag import create_agentic_rag_agent, query_agent

# Initialize agent
agent = create_agentic_rag_agent()

# Query
answer, response = query_agent(agent, "什么情况会被退学?")
print(answer)
```

## Architecture

### Offline Pipeline

```
Documents → Chunking → BM25 Encoding → Vectorization → Storage
                                    ↓
                            Vector Database (Chroma)
                            BM25 Model (Pickle)
```

### Online Pipeline (Agentic RAG)

```
User Query
    ↓
Agent Decision (RAG needed?)
    ↓ Yes
Query Rewriting (optional)
    ↓
Keyword Extraction
    ↓
Vector Retrieval (Top K)
    ↓
Keyword-based Re-ranking
    ↓
Document Summarization (if >1000 chars)
    ↓
Answer Generation
    ↓
Response to User
```

### Agent Tools

1. **expand_and_keyword**: Rewrites unclear queries and extracts keywords
2. **retrieval_augment**: Retrieves documents using vector search + keyword re-ranking
3. **summary_related_doc**: Filters and summarizes long documents

## Configuration

Edit `config.py` to customize:

- **Model Settings**: Embedding model, LLM API configuration
- **Chunking**: `CHUNK_SIZE`, `CHUNK_OVERLAP`
- **Retrieval**: `VECTOR_SEARCH_K`, `FINAL_RETRIEVAL_K`, `KEYWORD_BOOST_SCORE`
- **Agent**: `MAX_ITERATIONS`, `SUMMARY_THRESHOLD`
- **Paths**: Document paths, cache directories

## Project Structure

```
agentic-RAG/
├── config.py              # Configuration settings
├── offline_pipeline.py    # Knowledge base construction
├── agent_tools.py         # Agent tools (query rewrite, retrieval, summarization)
├── agentic_rag.py         # Main agentic RAG agent
├── main.py                # CLI entry point
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── documents/            # Document storage
│   └── sample_document.txt
└── rag_cache/            # Generated cache (created after first build)
    ├── chroma_db/        # Vector database
    └── bm25_model.pkl    # BM25 model
```

## How It Works

### Traditional RAG vs. Agentic RAG

**Traditional RAG:**
- Fixed pipeline: Query → Retrieve → Generate
- No query enhancement
- No iterative refinement
- Limited to single retrieval pass

**Agentic RAG:**
- LLM decides when to use RAG
- Query rewriting for unclear inputs
- Iterative refinement with retries
- Intelligent tool selection
- Document filtering and summarization

### Example Flow

1. **User asks**: "两周未参加学校活动会被退学吗?"
2. **Agent decides**: Query is related to knowledge base → Use RAG
3. **Tool 1 (expand_and_keyword)**: 
   - Expands query: "如果学生连续两周未参加学校规定的教学活动，会被退学吗？"
   - Extracts keyword: "退学"
4. **Tool 2 (retrieval_augment)**:
   - Vector search retrieves top 10 documents
   - Keyword "退学" boosts relevant documents
   - Returns top 5 most relevant chunks
5. **Tool 3 (summary_related_doc)** (if needed):
   - Filters chunks to most relevant parts
6. **Agent generates answer** based on retrieved context

## Customization

### Adding Custom Tools

1. Define your tool function in `agent_tools.py`
2. Decorate with `@tool` from `langchain.tools`
3. Add to tools list in `create_agentic_rag_agent()`
4. Update system prompt to instruct agent on when to use it

### Using Different Models

Update `config.py`:
- `EMBEDDING_MODEL_PATH`: Change embedding model
- `DEEPSEEK_MODEL`: Change LLM (if using different provider)
- Or modify `create_agentic_rag_agent()` to use different LLM class

### Supporting Other Languages

1. Replace `jieba` with appropriate tokenizer in `offline_pipeline.py`
2. Update prompts in `agent_tools.py` to your language
3. Adjust system prompt in `agentic_rag.py`

## Troubleshooting

### "Vectorstore not found"
- Run `python main.py --build` first to create the knowledge base

### "API key error"
- Set `DEEPSEEK_API_KEY` in `config.py` or as environment variable

### "No relevant documents found"
- Check if your query is related to the knowledge base
- Try rephrasing the query
- Verify documents were loaded correctly during build

### Slow performance
- Use GPU for embeddings: Set `device='cuda'` in `config.py`
- Reduce `VECTOR_SEARCH_K` for faster retrieval
- Use a smaller embedding model

## Advanced Features

### Tool Call Limits

You can add middleware to limit tool calls:

```python
from langchain.agents.middleware import ToolCallLimitMiddleware

agent = create_agent(
    model=model,
    tools=tools,
    middleware=[
        ToolCallLimitMiddleware(run_limit=10),
        ToolCallLimitMiddleware(tool_name="expand_and_keyword", run_limit=2),
    ]
)
```

### Memory Integration

Add conversation memory to maintain context across queries (future enhancement).

## License

MIT License

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Acknowledgments

This implementation is inspired by modern RAG architectures and agentic AI patterns, combining the best of retrieval systems with autonomous agent capabilities.
