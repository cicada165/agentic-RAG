"""
Configuration management for Deep Research Assistant
"""
import os
from typing import Optional, Literal
from dotenv import load_dotenv
from .exceptions import ConfigError

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment"""
    
    # API Keys (loaded from st.secrets or .env)
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default to cost-effective model
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_API_PROVIDER: Literal["tavily", "serper", "custom"] = "tavily"
    
    # Workflow Settings
    MAX_RESEARCH_ITERATIONS: int = 5
    MAX_SOURCES_PER_QUERY: int = 20
    MIN_RELEVANCE_SCORE: float = 0.3
    MAX_CONCURRENT_SEARCHES: int = 5
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT_SECONDS: int = 60
    
    # UI Settings
    STREAM_UPDATE_INTERVAL_MS: int = 500
    MAX_HISTORY_ITEMS: int = 10
    
    @classmethod
    def load(cls) -> "Config":
        """
        Loads configuration from environment variables.
        Prioritizes Streamlit secrets, falls back to .env file.
        
        Returns:
            Config: Configured instance
            
        Raises:
            ConfigError: If required API keys are missing
        """
        config = cls()
        
        # Try to load from Streamlit secrets first (if available)
        try:
            import streamlit as st
            # Check if we're in a Streamlit runtime context
            # Accessing st.secrets outside of Streamlit runtime raises an error
            try:
                if hasattr(st, 'secrets'):
                    secrets = st.secrets
                    # Only access if secrets file exists (check without triggering error)
                    if secrets:
                        config.OPENAI_API_KEY = secrets.get("OPENAI_API_KEY", "")
                        config.OPENAI_MODEL = secrets.get("OPENAI_MODEL", "gpt-4o-mini")
                        config.SEARCH_API_KEY = secrets.get("SEARCH_API_KEY", "")
                        config.SEARCH_API_PROVIDER = secrets.get("SEARCH_API_PROVIDER", "tavily")
            except Exception:
                # Not in Streamlit runtime context or secrets not available
                # Fall through to environment variables
                pass
        except (ImportError, AttributeError):
            # Streamlit not installed or not available, use environment variables
            pass
        
        # Fall back to environment variables
        if not hasattr(config, 'OPENAI_API_KEY') or not config.OPENAI_API_KEY:
            config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        
        if not hasattr(config, 'OPENAI_MODEL') or not config.OPENAI_MODEL:
            config.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        if not config.SEARCH_API_KEY:
            config.SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
        
        # Load search provider from environment if not already set from secrets
        # Only override if it's still the default "tavily" (meaning it wasn't set from secrets)
        if not hasattr(config, 'SEARCH_API_PROVIDER') or config.SEARCH_API_PROVIDER == "tavily":
            env_provider = os.getenv("SEARCH_API_PROVIDER", "tavily")
            if env_provider in ["tavily", "serper", "custom"]:
                config.SEARCH_API_PROVIDER = env_provider
        
        # Load other settings from environment with defaults
        config.MAX_RESEARCH_ITERATIONS = int(os.getenv("MAX_RESEARCH_ITERATIONS", "5"))
        config.MAX_SOURCES_PER_QUERY = int(os.getenv("MAX_SOURCES_PER_QUERY", "20"))
        config.MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.3"))
        config.MAX_CONCURRENT_SEARCHES = int(os.getenv("MAX_CONCURRENT_SEARCHES", "5"))
        config.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        config.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
        config.LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        config.STREAM_UPDATE_INTERVAL_MS = int(os.getenv("STREAM_UPDATE_INTERVAL_MS", "500"))
        config.MAX_HISTORY_ITEMS = int(os.getenv("MAX_HISTORY_ITEMS", "10"))
        
        # Validate required API keys
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your-api-key-here":
            raise ConfigError(
                "OPENAI_API_KEY is required. Set it in .env file or Streamlit secrets."
            )
        
        return config
