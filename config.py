# ============================================================================
# FILE: config.py (Configuration Settings)
# ============================================================================

"""
Configuration settings for VibrationVIEW API
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    # API Settings
    API_VERSION = os.environ.get('API_VERSION') or '1.0.0'
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # CORS Settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or '*'
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    
    # VibrationVIEW Settings
    VV_CONNECTION_TIMEOUT = float(os.environ.get('VV_CONNECTION_TIMEOUT') or '10.0')
    VV_RETRY_ATTEMPTS = int(os.environ.get('VV_RETRY_ATTEMPTS') or '5')
    VV_MAX_INSTANCES = int(os.environ.get('VV_MAX_INSTANCES') or '5')

    # VibrationVIEW folders
    PROFILE_FOLDER = 'C:\\VibrationVIEW\\Profiles'
    REPORT_FOLDER = 'C:\\VibrationVIEW\\Reports'
    EXE_NAME = 'C:\\Program Files\\VibrationVIEW 2025\\VibrationVIEW.exe'
    
    # Flask Settings
    TESTING = False
    DEBUG = False

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

