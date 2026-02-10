
import os
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config import Config
from src.agents.orchestrator import create_research_graph
from src.models import ResearchState

def test_config_loading():
    """Test that config loads correctly from .env"""
    print("Testing Config Loading...")
    try:
        config = Config.load()
        print(f"Loaded key: {config.LLM_API_KEY}")
        assert config.LLM_API_KEY == "your-api-key-here"
        print("✅ Config loaded successfully")
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        # print full traceback
        import traceback
        traceback.print_exc()
        raise

def test_graph_creation():
    """Test that research graph can be created"""
    print("Testing Graph Creation...")
    try:
        graph = create_research_graph()
        if graph:
            print("✅ Graph created successfully")
        else:
            print("⚠️ Graph creation returned None (fallback mode)")
    except Exception as e:
        print(f"❌ Graph creation failed: {e}")
        raise

async def test_workflow_dry_run():
    """Test dry run of workflow components"""
    print("Testing Workflow Components...")
    
    # Mock LLM client to avoid API calls
    with patch('src.utils.llm_client.create_llm_client') as mock_create_llm:
        mock_llm = MagicMock()
        mock_llm.ainvoke.return_value.content = "Test query 1\nTest query 2"
        mock_create_llm.return_value = mock_llm
        
        from src.agents.research_agent import generate_search_queries
        
        queries = await generate_search_queries("test query", llm_client=mock_llm)
        assert len(queries) > 0
        print("✅ Query generation tested")

if __name__ == "__main__":
    try:
        test_config_loading()
        test_graph_creation()
        asyncio.run(test_workflow_dry_run())
        print("\n🎉 All smoke tests passed!")
    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        sys.exit(1)
