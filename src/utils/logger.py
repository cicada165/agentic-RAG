"""
Logging utilities for Deep Research Assistant
"""
import logging
import sys


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Sets up structured logger for application.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Avoid adding multiple handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
