# app/config/test.py

from .base import BaseConfig

class TestConfig(BaseConfig):
    """Test configuration."""
    
    DEBUG = False
    TESTING = True
    
    # Test-specific settings
    UPLOAD_FOLDER = 'test_uploads'
    OUTPUT_FOLDER = 'test_output'
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1 MB limit for testing
