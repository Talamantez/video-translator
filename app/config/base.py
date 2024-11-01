# app/config/base.py

import os
from typing import Dict, Any

class BaseConfig:
    """Base configuration class with common settings."""
    
    # Application settings
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')

    # File handling
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    OUTPUT_FOLDER = os.path.join(os.getcwd(), 'output')
    SAVED_RESULTS_FOLDER = os.path.join(os.getcwd(), 'saved_results')
    ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 * 1024  # 16 GB limit

    # Processing settings
    DEFAULT_CLIP_DURATION = 30  # seconds
    DEFAULT_TARGET_LANGUAGE = 'en'
    
    # ML Model settings
    YOLO_MODEL_PATH = 'yolov8n.pt'
    CONFIDENCE_THRESHOLD = 0.5

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return {
            key: value for key, value in cls.__dict__.items() 
            if not key.startswith('_')
        }