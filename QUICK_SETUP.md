# Quick Setup - OpenAI Configuration

## 🚀 Fast Setup (For Agent Environment/Kernel)

Since you're using the agent environment/kernel with packages already installed, you just need to set your OpenAI API key:

### Option 1: Set Environment Variable (Recommended)
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Option 2: Create .env file
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your-api-key-here
```

### Option 3: Set in Python (Temporary - for testing only)
```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key-here"
```

## ✅ Verify Setup

Run this to verify your configuration:
```python
from src.utils.config import Config
config = Config.load()
print(f"OpenAI Model: {config.OPENAI_MODEL}")
print(f"API Key configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
```

## 📝 Next Steps

1. Set your API key using one of the methods above
2. Install any missing packages: `pip install langchain-openai`
3. Run the Streamlit app: `streamlit run src/main.py`

## 🔒 Security Note

**IMPORTANT**: The API key shown above should be:
- Rotated/regenerated if it was exposed
- Never committed to git
- Stored securely in environment variables or `.env` file (which is gitignored)
