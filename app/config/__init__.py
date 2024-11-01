# app/config/__init__.py

import os
from typing import Type
from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .test import TestConfig

def get_config() -> Type[BaseConfig]:
    """Get the appropriate configuration based on environment."""
    env = os.environ.get('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestConfig
    }
    return configs.get(env, DevelopmentConfig)