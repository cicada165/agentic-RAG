# Quick Start Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure API Key

Edit `config.py` and set your DeepSeek API key:

```python
DEEPSEEK_API_KEY = "your-actual-api-key-here"
```

Or set it as an environment variable:

```bash
export DEEPSEEK_API_KEY="your-actual-api-key-here"
```

## Step 3: Build Knowledge Base

```bash
python main.py --build
```

This will:
- Load documents from `documents/sample_document.txt`
- Create chunks, BM25 model, and vector embeddings
- Save everything to `rag_cache/`

## Step 4: Start Querying

### Interactive Mode (Recommended)
```bash
python main.py --interactive
```

### Single Query
```bash
python main.py --query "什么情况会被退学?"
```

### Python Script
```python
from agentic_rag import create_agentic_rag_agent, query_agent

agent = create_agentic_rag_agent()
answer, _ = query_agent(agent, "什么情况会被退学?")
print(answer)
```

## Troubleshooting

**"Vectorstore not found"**
→ Run `python main.py --build` first

**"API key error"**
→ Set `DEEPSEEK_API_KEY` in config.py or environment

**"No module named 'langchain'"**
→ Run `pip install -r requirements.txt`

## Next Steps

- Add your own documents to `documents/` folder
- Customize retrieval parameters in `config.py`
- Add custom tools in `agent_tools.py`
- Modify system prompt in `agentic_rag.py` for different behavior
