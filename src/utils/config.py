"""
Configuration management for Deep Research Assistant
"""
import os
from typing import Optional, Literal
from dotenv import load_dotenv
from .exceptions import ConfigError

# Load environment variables from .env file
try:
    load_dotenv()
except (PermissionError, OSError) as e:
    # If .env exists but is not readable (e.g. permission issues), continue
    # We'll rely on existing environment variables or secrets
    pass


class Config:
    """Application configuration loaded from environment"""
    
    # API Keys (loaded from st.secrets or .env)
    # CRITICAL: No hardcoded defaults - must raise ConfigError if missing
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_MODEL: str = "deepseek-chat"
    
    SEARCH_API_KEY: Optional[str] = None
    SEARCH_API_PROVIDER: Literal["tavily", "serper", "custom"] = "tavily"
    TAVILY_API_KEY: Optional[str] = None  # Specific key for Tavily if used
    
    # Workflow Settings
    MAX_RESEARCH_ITERATIONS: int = 5
    MAX_SOURCES_PER_QUERY: int = 20
    MAX_SEARCH_QUERIES: int = 5
    MIN_RELEVANCE_SCORE: float = 0.3
    MAX_CONCURRENT_SEARCHES: int = 5
    MIN_VERIFIED_SOURCES: int = 2
    MIN_SOURCE_SNIPPET_LENGTH: int = 50
    VERIFICATION_FALLBACK_RELEVANCE: float = 0.4
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT_SECONDS: int = 60
    
    # UI Settings
    STREAM_UPDATE_INTERVAL_MS: int = 500
    MAX_HISTORY_ITEMS: int = 10
    
    # Cache Settings
    CACHE_TTL_VERIFICATION_HOURS: int = 24
    CACHE_TTL_QUERY_HOURS: int = 1

    
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
                        if "LLM_API_KEY" in secrets:
                            config.LLM_API_KEY = secrets["LLM_API_KEY"]
                            secrets_loaded.add("LLM_API_KEY")
                        elif "DEEPSEEK_API_KEY" in secrets: # Backward compatibility
                             config.LLM_API_KEY = secrets["DEEPSEEK_API_KEY"]
                             secrets_loaded.add("LLM_API_KEY")

                        if "LLM_MODEL" in secrets:
                            config.LLM_MODEL = secrets["LLM_MODEL"]
                            secrets_loaded.add("LLM_MODEL")
                        elif "DEEPSEEK_MODEL" in secrets: # Backward compatibility
                            config.LLM_MODEL = secrets["DEEPSEEK_MODEL"]
                            secrets_loaded.add("LLM_MODEL")

                        if "LLM_BASE_URL" in secrets:
                            config.LLM_BASE_URL = secrets["LLM_BASE_URL"]
                            secrets_loaded.add("LLM_BASE_URL")
                            
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
        
        if "LLM_API_KEY" not in secrets_loaded:
            # Check LLM_API_KEY first, then fallback to DEEPSEEK_API_KEY
            config.LLM_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
        
        if "LLM_MODEL" not in secrets_loaded:
            # Check LLM_MODEL first, then fallback to DEEPSEEK_MODEL
            config.LLM_MODEL = os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if "LLM_BASE_URL" not in secrets_loaded:
             config.LLM_BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            
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
                config.SEARCH_API_PROVIDER = env_provider  # type: ignore
        
        # Load other settings from environment with defaults
        config.MAX_RESEARCH_ITERATIONS = int(os.getenv("MAX_RESEARCH_ITERATIONS", "5"))
        config.MAX_SOURCES_PER_QUERY = int(os.getenv("MAX_SOURCES_PER_QUERY", "20"))
        config.MAX_SEARCH_QUERIES = int(os.getenv("MAX_SEARCH_QUERIES", "5"))
        config.MIN_RELEVANCE_SCORE = float(os.getenv("MIN_RELEVANCE_SCORE", "0.3"))
        config.MAX_CONCURRENT_SEARCHES = int(os.getenv("MAX_CONCURRENT_SEARCHES", "5"))
        config.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        config.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4000"))
        config.LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        config.STREAM_UPDATE_INTERVAL_MS = int(os.getenv("STREAM_UPDATE_INTERVAL_MS", "500"))
        config.MAX_HISTORY_ITEMS = int(os.getenv("MAX_HISTORY_ITEMS", "10"))
        config.MIN_VERIFIED_SOURCES = int(os.getenv("MIN_VERIFIED_SOURCES", "2"))
        config.MIN_SOURCE_SNIPPET_LENGTH = int(os.getenv("MIN_SOURCE_SNIPPET_LENGTH", "50"))
        config.VERIFICATION_FALLBACK_RELEVANCE = float(os.getenv("VERIFICATION_FALLBACK_RELEVANCE", "0.4"))
        
        # Ensure SEARCH_API_KEY is populated if TAVILY_API_KEY is present and provider is tavily
        if config.SEARCH_API_PROVIDER == "tavily" and not config.SEARCH_API_KEY and config.TAVILY_API_KEY:
            config.SEARCH_API_KEY = config.TAVILY_API_KEY
        
        # Validate required API keys
        if not hasattr(config, 'LLM_API_KEY') or not config.LLM_API_KEY or config.LLM_API_KEY == "your-api-key-here":
            raise ConfigError(
                "LLM_API_KEY is required. Set it in .env file or Streamlit secrets."
            )
            
        return config
