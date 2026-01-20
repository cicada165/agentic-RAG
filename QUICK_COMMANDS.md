# Quick Commands Reference

## 🧪 Testing

```bash
# Run comprehensive test suite
python3 test_setup.py

# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## 🚀 Running the App

```bash
# Start Streamlit app
streamlit run streamlit_app.py

# Or run directly
streamlit run src/main.py
```

## 🔧 Setup

```bash
# Install dependencies
pip3 install -r requirements.txt

# Verify configuration
python3 -c "from src.utils.config import Config; c = Config.load(); print(f'Model: {c.OPENAI_MODEL}')"
```

## 📝 Python Command Notes

**macOS/Linux**: Use `python3` (not `python`)
**Windows**: May use `python` or `python3`

To check which command works:
```bash
which python3    # Shows path if available
python3 --version  # Shows version
```
