# Testing Guide - Deep Research Assistant

## ✅ Quick Test (Recommended)

Run the comprehensive test suite:

```bash
# On macOS/Linux (use python3)
python3 test_setup.py

# On Windows or if python is available
python test_setup.py
```

This will test:
- ✅ All imports
- ✅ Configuration loading
- ✅ Data models
- ✅ Agent imports
- ✅ UI components
- ✅ LLM client creation

**Expected Output**: All tests should pass ✅

---

## 🧪 Unit Tests

Run the pytest test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

**Current Test Files**:
- `tests/test_config.py` - Configuration tests
- `tests/test_models.py` - Data model tests
- `tests/test_research_agent.py` - Research agent tests

---

## 🚀 Test the Streamlit App

### Option 1: Run the Main App
```bash
streamlit run streamlit_app.py
```

Or:
```bash
streamlit run src/main.py
```

### Option 2: Test Configuration Loading
```python
from src.utils.config import Config

config = Config.load()
print(f"Model: {config.OPENAI_MODEL}")
print(f"API Key configured: {bool(config.OPENAI_API_KEY)}")
```

### Option 3: Test LLM Client
```python
from src.utils.llm_client import create_llm_client

client = create_llm_client()
print(f"Client created: {client.model_name}")
```

---

## 🔍 Test OpenAI API Connection

To test the actual OpenAI API (uses API credits):

```bash
# Set environment variable to enable API test
TEST_API_CALL=1 python test_setup.py
```

Or test manually:
```python
from src.utils.llm_client import create_llm_client

client = create_llm_client()
response = client.invoke("Say 'Hello' in one word.")
print(response.content)
```

---

## 📋 Test Checklist

### Basic Setup Tests
- [ ] Configuration loads without errors
- [ ] OPENAI_API_KEY is set and valid
- [ ] All imports work
- [ ] Data models can be instantiated

### Component Tests
- [ ] LLM client can be created
- [ ] Research agent imports successfully
- [ ] Reviewer agent imports successfully
- [ ] Writer agent imports successfully
- [ ] UI components import successfully

### Integration Tests
- [ ] Streamlit app starts without errors
- [ ] Configuration shows in sidebar
- [ ] Can submit a query (even if it fails, UI should work)

### API Tests (Optional)
- [ ] OpenAI API responds to simple queries
- [ ] Search API works (if SEARCH_API_KEY is set)

---

## 🐛 Troubleshooting

### Configuration Errors
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Or check .env file
cat .env | grep OPENAI_API_KEY
```

### Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Specifically for OpenAI
pip install langchain-openai
```

### Streamlit Errors
```bash
# Check Streamlit version
streamlit --version

# Update if needed
pip install --upgrade streamlit
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -v

# Run with print statements
pytest tests/ -v -s

# Run specific test
pytest tests/test_config.py::test_config_load_with_env_vars -v
```

---

## 🎯 Expected Test Results

### test_setup.py
```
✅ Imports: PASSED
✅ Configuration: PASSED
✅ Data Models: PASSED
✅ Agents: PASSED
✅ UI Components: PASSED
✅ LLM Client: PASSED
⏭️  OpenAI API: SKIPPED (or PASSED if TEST_API_CALL=1)
```

### pytest tests/
```
tests/test_config.py::test_config_load_with_env_vars PASSED
tests/test_config.py::test_config_load_missing_api_key PASSED
tests/test_config.py::test_config_default_values PASSED
```

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Start the Streamlit app**:
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Try a research query**:
   - Open the app in your browser
   - Enter a research question
   - Watch the research workflow execute

3. **Check the logs**:
   - Look for any errors in the terminal
   - Check the Streamlit UI for error messages

---

## 📝 Test Scripts

### Quick Verification Script
```python
# quick_test.py
from src.utils.config import Config
from src.utils.llm_client import create_llm_client

print("Testing configuration...")
config = Config.load()
print(f"✅ Config loaded: {config.OPENAI_MODEL}")

print("Testing LLM client...")
client = create_llm_client()
print(f"✅ Client created: {client.model_name}")

print("🎉 All basic tests passed!")
```

Run it:
```bash
python quick_test.py
```

---

## 🔒 Security Note

When testing with real API calls:
- Monitor your OpenAI API usage
- Set usage limits in OpenAI dashboard
- Use test API keys for development
- Never commit API keys to version control

---

## 📚 Additional Resources

- **Test Setup**: `test_setup.py` - Comprehensive test suite
- **Unit Tests**: `tests/` directory
- **Configuration**: `src/utils/config.py`
- **LLM Client**: `src/utils/llm_client.py`
