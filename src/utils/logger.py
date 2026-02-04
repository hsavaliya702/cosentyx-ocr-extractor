"""Logging configuration for the application."""
import logging
import sys
from typing import Optional

from config.settings import get_settings

settings = get_settings()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance.
    
    Args:
        name: Logger name (defaults to root logger if None)
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name or __name__)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, settings.log_level.upper()))
        
        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger
