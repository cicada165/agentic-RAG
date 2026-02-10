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
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_API_PROVIDER: Literal["tavily", "serper", "custom"] = "tavily"
    TAVILY_API_KEY: Optional[str] = None  # Specific key for Tavily if used
    
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
        
        # Track what was loaded from secrets to avoid overriding with env vars if present
        secrets_loaded = set()
        
        # Try to load from Streamlit secrets first (if available)
        try:
            import streamlit as st
            # Check if we're in a Streamlit runtime context
            try:
                if hasattr(st, 'secrets'):
                    secrets = st.secrets
                    if secrets:
                        if "DEEPSEEK_API_KEY" in secrets:
                            config.DEEPSEEK_API_KEY = secrets["DEEPSEEK_API_KEY"]
                            secrets_loaded.add("DEEPSEEK_API_KEY")
                        
                        if "DEEPSEEK_MODEL" in secrets:
                            config.DEEPSEEK_MODEL = secrets["DEEPSEEK_MODEL"]
                            secrets_loaded.add("DEEPSEEK_MODEL")
                            
                        if "SEARCH_API_KEY" in secrets:
                            config.SEARCH_API_KEY = secrets["SEARCH_API_KEY"]
                            secrets_loaded.add("SEARCH_API_KEY")
                            
                        if "SEARCH_API_PROVIDER" in secrets:
                            config.SEARCH_API_PROVIDER = secrets["SEARCH_API_PROVIDER"]
                            secrets_loaded.add("SEARCH_API_PROVIDER")
                            
                        if "TAVILY_API_KEY" in secrets:
                            config.TAVILY_API_KEY = secrets["TAVILY_API_KEY"]
                            secrets_loaded.add("TAVILY_API_KEY")
            except Exception:
                # Not in Streamlit runtime context or secrets not available
                pass
        except (ImportError, AttributeError):
            pass
        
        # Fall back to environment variables for anything not loaded from secrets
        
        if "DEEPSEEK_API_KEY" not in secrets_loaded:
            config.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        
        if "DEEPSEEK_MODEL" not in secrets_loaded:
            config.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            
        if "SEARCH_API_KEY" not in secrets_loaded:
            config.SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
            
        if "TAVILY_API_KEY" not in secrets_loaded:
             config.TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

        # Provider logic: 
        # 1. If secrets set it, use that (done above).
        # 2. If not, check env var.
        # 3. If neither, default (tavily) remains.
        if "SEARCH_API_PROVIDER" not in secrets_loaded:
            env_provider = os.getenv("SEARCH_API_PROVIDER")
            if env_provider and env_provider in ["tavily", "serper", "custom"]:
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
        
        # Ensure SEARCH_API_KEY is populated if TAVILY_API_KEY is present and provider is tavily
        if config.SEARCH_API_PROVIDER == "tavily" and not config.SEARCH_API_KEY and config.TAVILY_API_KEY:
            config.SEARCH_API_KEY = config.TAVILY_API_KEY
        
        # Validate required API keys
        if not hasattr(config, 'DEEPSEEK_API_KEY') or not config.DEEPSEEK_API_KEY or config.DEEPSEEK_API_KEY == "your-api-key-here":
            raise ConfigError(
                "DEEPSEEK_API_KEY is required. Set it in .env file or Streamlit secrets."
            )
            
        return config
