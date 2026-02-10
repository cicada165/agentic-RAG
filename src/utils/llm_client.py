"""
LLM Client Utility - Creates OpenAI/DeepSeek client instances
"""
from typing import Optional
from ..utils.config import Config
from ..utils.exceptions import LLMException, ConfigError

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None


def create_llm_client(
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None
):
    """
    Creates an OpenAI-compatible LLM client instance (configured for configured provider).
    
    Args:
        model: Model name (defaults to config.LLM_MODEL)
        temperature: Temperature setting (defaults to config.LLM_TEMPERATURE)
        max_tokens: Max tokens (defaults to config.LLM_MAX_TOKENS)
        timeout: Timeout in seconds (defaults to config.LLM_TIMEOUT_SECONDS)
        
    Returns:
        ChatOpenAI: Configured OpenAI client instance
        
    Raises:
        ConfigError: If LLM API key is not configured
        ImportError: If langchain-openai is not installed
    """
    if ChatOpenAI is None:
        raise ImportError(
            "langchain-openai is not installed. Install it with: pip install langchain-openai"
        )
    
    config = Config.load()
    
    # Use provided values or fall back to config defaults
    model_name = model or config.LLM_MODEL
    temp = temperature if temperature is not None else config.LLM_TEMPERATURE
    max_toks = max_tokens or config.LLM_MAX_TOKENS
    timeout_sec = timeout or config.LLM_TIMEOUT_SECONDS
    
    # Validate API key
    if not config.LLM_API_KEY:
        raise ConfigError(
            "LLM_API_KEY is required. Set it in .env file or Streamlit secrets."
        )
    
    try:
        client = ChatOpenAI(
            model=model_name,
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
            temperature=temp,
            max_tokens=max_toks,
            timeout=timeout_sec
        )
        return client
    except Exception as e:
        raise LLMException(f"Failed to create LLM client: {str(e)}")
