"""
Comprehensive test script to verify the project is set up correctly
Run this to test: python test_setup.py
"""
import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    try:
        from src.utils.config import Config, ConfigError
        from src.utils.llm_client import create_llm_client
        from src.models import ResearchState, ResearchStatus, Source
        from src.utils.exceptions import ConfigError, LLMException, SearchAPIException
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    try:
        from src.utils.config import Config
        
        config = Config.load()
        
        # Check required fields
        assert hasattr(config, 'OPENAI_API_KEY'), "OPENAI_API_KEY not found"
        assert config.OPENAI_API_KEY, "OPENAI_API_KEY is empty"
        assert hasattr(config, 'OPENAI_MODEL'), "OPENAI_MODEL not found"
        assert config.OPENAI_MODEL, "OPENAI_MODEL is empty"
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Model: {config.OPENAI_MODEL}")
        print(f"   API Key: {'*' * 20}...{config.OPENAI_API_KEY[-4:]}")
        print(f"   Max Sources: {config.MAX_SOURCES_PER_QUERY}")
        print(f"   Max Iterations: {config.MAX_RESEARCH_ITERATIONS}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_llm_client():
    """Test LLM client creation"""
    print("\n🔍 Testing LLM client...")
    try:
        from src.utils.llm_client import create_llm_client
        
        client = create_llm_client()
        
        assert client is not None, "LLM client is None"
        print(f"✅ LLM client created successfully")
        print(f"   Model: {client.model_name}")
        print(f"   Temperature: {client.temperature}")
        print(f"   Max Tokens: {client.max_tokens}")
        return True
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        print(f"   Make sure OPENAI_API_KEY is set and langchain-openai is installed")
        return False

def test_models():
    """Test Pydantic models"""
    print("\n🔍 Testing data models...")
    try:
        from src.models import ResearchState, ResearchStatus, Source
        from datetime import datetime
        
        # Test Source model
        source = Source(
            url="https://example.com",
            title="Test Source",
            snippet="This is a test snippet",
            relevance_score=0.8
        )
        assert source.url == "https://example.com"
        
        # Test ResearchState model
        state = ResearchState(
            query="Test query",
            query_id="test-123",
            status=ResearchStatus.PENDING
        )
        assert state.query == "Test query"
        assert state.status == ResearchStatus.PENDING
        
        print("✅ Data models working correctly")
        return True
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def test_agents():
    """Test agent imports"""
    print("\n🔍 Testing agent imports...")
    try:
        from src.agents.research_agent import perform_web_search, generate_search_queries
        from src.agents.reviewer_agent import verify_source, detect_conflicts
        from src.agents.writer_agent import generate_report
        from src.agents.orchestrator import create_research_graph
        
        print("✅ All agents imported successfully")
        return True
    except Exception as e:
        print(f"❌ Agent import test failed: {e}")
        return False

def test_components():
    """Test UI component imports"""
    print("\n🔍 Testing UI components...")
    try:
        from src.components.chat_interface import (
            render_chat_input,
            render_message_history,
            render_status_panel,
            render_report_viewer,
            render_error_message
        )
        
        print("✅ UI components imported successfully")
        return True
    except Exception as e:
        print(f"❌ Component import test failed: {e}")
        return False

def test_simple_llm_call():
    """Test a simple LLM API call"""
    print("\n🔍 Testing OpenAI API connection...")
    try:
        from src.utils.llm_client import create_llm_client
        
        client = create_llm_client()
        
        # Make a simple test call
        response = client.invoke("Say 'Hello, OpenAI!' in one word.")
        result = response.content if hasattr(response, 'content') else str(response)
        
        print(f"✅ OpenAI API connection successful")
        print(f"   Response: {result[:50]}...")
        return True
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        print(f"   This might be due to:")
        print(f"   - Invalid API key")
        print(f"   - Network issues")
        print(f"   - API rate limits")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Deep Research Assistant - Setup Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Data Models", test_models()))
    results.append(("Agents", test_agents()))
    results.append(("UI Components", test_components()))
    results.append(("LLM Client", test_llm_client()))
    
    # Optional: Test actual API call (may cost money)
    # Skip by default in non-interactive mode, set TEST_API_CALL=1 to enable
    print("\n" + "=" * 60)
    test_api = os.getenv("TEST_API_CALL", "0") == "1"
    if test_api:
        print("Testing OpenAI API call (API credits will be used)...")
        results.append(("OpenAI API", test_simple_llm_call()))
    else:
        print("⏭️  Skipping API call test (set TEST_API_CALL=1 to enable)")
        results.append(("OpenAI API", None))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⏭️  {test_name}: SKIPPED")
    
    print("\n" + "=" * 60)
    print(f"Total: {passed} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed! Your setup is ready.")
        print("\n🚀 Next steps:")
        print("   1. Run Streamlit app: streamlit run streamlit_app.py")
        print("   2. Or run tests: pytest tests/")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
