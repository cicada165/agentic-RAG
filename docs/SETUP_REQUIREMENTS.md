# Setup Requirements - Deep Research Assistant

## 🔑 Required API Keys

### 1. OpenAI API Key (REQUIRED)
- **What it's for**: LLM (Language Model) operations - generating search queries, reviewing sources, writing reports
- **Where to get it**: https://platform.openai.com/api-keys
- **Cost**: Check OpenAI pricing (gpt-4o-mini is cost-effective)
- **Environment Variable**: `OPENAI_API_KEY`
- **Default Model**: `gpt-4o-mini` (can be changed via `OPENAI_MODEL` env var)

### 2. Search API Key (OPTIONAL but Recommended)
- **What it's for**: Web search functionality - finding sources for research queries
- **Options**:
  - **Tavily** (Recommended): https://tavily.com/ - Specialized for AI research
  - **Serper**: https://serper.dev/ - Google search API alternative
- **Environment Variable**: `SEARCH_API_KEY`
- **Provider Setting**: `SEARCH_API_PROVIDER=tavily` or `SEARCH_API_PROVIDER=serper`

**Note**: If you don't provide a search API key, the system will use mock results for testing (not real web searches).

---

## 📝 Setup Instructions

### Step 1: Create `.env` file
Create a `.env` file in the project root with the following content:

```bash
# Required
OPENAI_API_KEY=your-actual-openai-api-key-here

# Optional: Change model (default is gpt-4o-mini)
# OPENAI_MODEL=gpt-4o-mini

# Optional but recommended for web search
SEARCH_API_KEY=your-tavily-or-serper-api-key-here
SEARCH_API_PROVIDER=tavily
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Verify Configuration
The system will automatically:
- Load from `.env` file (local development)
- Load from Streamlit secrets (if deployed on Streamlit Cloud)
- Show clear error messages if required keys are missing

---

## ✅ What You Need to Provide

### Minimum Setup (Basic Testing)
- ✅ **OPENAI_API_KEY** - Required for LLM operations

### Full Setup (Production Ready)
- ✅ **OPENAI_API_KEY** - Required
- ✅ **SEARCH_API_KEY** - Required for real web search
- ✅ **SEARCH_API_PROVIDER** - Set to "tavily" or "serper"

---

## 🚨 Important Notes

1. **OpenAI API Key Required**: This project uses OpenAI API (default model: gpt-4o-mini)
2. **Search API is Optional**: Without it, you'll get mock search results (good for testing)
3. **Never Commit Keys**: The `.env` file should be in `.gitignore` (already configured)
4. **Streamlit Cloud**: If deploying to Streamlit Cloud, use `st.secrets` instead of `.env`
5. **Security**: Never share your API key in code or commit it to version control

---

## 🔍 Current Status

- ✅ Configuration system is set up
- ✅ Error handling for missing keys is implemented
- ⚠️ `.env.example` file needs to be created (TODO item)

---

## 📚 Additional Resources

- OpenAI API Docs: https://platform.openai.com/docs/
- OpenAI Models: https://platform.openai.com/docs/models
- Tavily API Docs: https://docs.tavily.com/
- Serper API Docs: https://serper.dev/api-docs
