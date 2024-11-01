# app/config/production.py

from .base import BaseConfig

class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    LOG_LEVEL = 'INFO'
    ENABLE_DEBUG_TOOLBAR = False
    
    # Security settings
    ENABLE_RATE_LIMITING = True
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 3600  # 1 hour