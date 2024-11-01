# app/config/development.py

from .base import BaseConfig

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Override settings for development
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024 * 1024  # 4 GB limit for development
    
    # Additional development settings
    ENABLE_DEBUG_TOOLBAR = True
    LOG_LEVEL = 'DEBUG'