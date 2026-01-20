"""
Exception classes for Deep Research Assistant
"""


class ResearchException(Exception):
    """Base exception for research workflow"""
    pass


class SearchAPIException(ResearchException):
    """Exception for search API failures"""
    pass


class LLMException(ResearchException):
    """Exception for LLM API failures"""
    pass


class ConfigError(ResearchException):
    """Exception for configuration errors"""
    pass


class ValidationError(ResearchException):
    """Exception for data validation errors"""
    pass
