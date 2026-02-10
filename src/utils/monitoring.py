
from typing import Dict, Any, Optional
from .logger import setup_logger
from ..models import TokenUsage

logger = setup_logger(__name__)

# Model pricing per 1M tokens (as of Feb 2026 estimation)
# Input / Output prices
MODEL_PRICING = {
    "deepseek-chat": (0.07, 1.10),      # DeepSeek V3/R1 estimation
    "deepseek-reasoner": (0.55, 2.19),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "github-models": (0.0, 0.0),       # Assuming free tier for testing or user provided
}

class UsageTracker:
    """Helper for tracking token usage and calculating costs"""
    
    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculates estimated cost in USD"""
        # Default to gpt-4o pricing if unknown
        pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["gpt-4o"])
        
        input_cost = (prompt_tokens / 1_000_000) * pricing[0]
        output_cost = (completion_tokens / 1_000_000) * pricing[1]
        
        return input_cost + output_cost

    @staticmethod
    def extract_usage(response: Any, model_name: str) -> TokenUsage:
        """Extracts token usage from LangChain response metadata"""
        try:
            # LangChain response often has response_metadata
            metadata = getattr(response, "response_metadata", {})
            token_usage = metadata.get("token_usage", {})
            
            if not token_usage:
                # Fallback for different LangChain versions/providers
                token_usage = metadata.get("usage", {})
                
            prompt = token_usage.get("prompt_tokens", 0)
            completion = token_usage.get("completion_tokens", 0)
            total = token_usage.get("total_tokens", prompt + completion)
            
            cost = UsageTracker.calculate_cost(model_name, prompt, completion)
            
            return TokenUsage(
                prompt_tokens=prompt,
                completion_tokens=completion,
                total_tokens=total,
                estimated_cost_usd=cost
            )
        except Exception as e:
            logger.warning(f"Failed to extract usage from response: {e}")
            return TokenUsage()
