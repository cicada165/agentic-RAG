"""
Tests for configuration management
"""
import os
import pytest
from src.utils.config import Config
from src.utils.exceptions import ConfigError


def test_config_load_with_env_vars(monkeypatch):
    """Test Config.load() with environment variables"""
    # Set environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setenv("SEARCH_API_KEY", "search-key-456")
    monkeypatch.setenv("SEARCH_API_PROVIDER", "tavily")
    
    config = Config.load()
    
    assert config.OPENAI_API_KEY == "test-key-123"
    assert config.SEARCH_API_KEY == "search-key-456"
    assert config.SEARCH_API_PROVIDER == "tavily"
    assert config.OPENAI_MODEL == "gpt-4o-mini"  # Default model
    assert config.MAX_RESEARCH_ITERATIONS == 5


def test_config_load_missing_api_key(monkeypatch):
    """Test Config.load() raises error when API key is missing"""
    # Remove OPENAI_API_KEY
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    
    with pytest.raises(ConfigError):
        Config.load()


def test_config_default_values(monkeypatch):
    """Test Config default values"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    
    config = Config.load()
    
    assert config.MAX_SOURCES_PER_QUERY == 20
    assert config.MIN_RELEVANCE_SCORE == 0.3
    assert config.LLM_TEMPERATURE == 0.7
    assert config.LLM_MAX_TOKENS == 4000
    assert config.OPENAI_MODEL == "gpt-4o-mini"
