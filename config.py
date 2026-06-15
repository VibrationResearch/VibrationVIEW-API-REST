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

    # CORS Settings — controls which browser origins may make cross-origin
    # requests to the API.  Set to http://127.0.0.1 to block unexpected browser
    # access.
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS') or 'http://127.0.0.1'

    # API Key Authentication
    # Generate a key with: python -c "import secrets; print(secrets.token_hex(32))"
    API_KEY = os.environ.get('API_KEY') or ''

    # Allow GET requests on state-changing endpoints (start, stop, save, etc.).
    # Set to true for backward compatibility or demonstrations only.
    ALLOW_GET_WRITE = (os.environ.get('ALLOW_GET_WRITE') or 'false').lower() in ('true', '1', 'yes')

    # Maximum request body size. Flask rejects requests larger than this before
    # they reach application code, preventing memory exhaustion from oversized uploads.
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 10 * 1024 * 1024)

    # Logging — VV_LOG_DIR is resolved to an absolute path so logs are
    # written to a predictable location regardless of the working directory.
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    VV_LOG_DIR = os.path.abspath(
        os.environ.get('VV_LOG_DIR') or r'C:\ProgramData\VibrationVIEW\logs'
    )
    VV_LOG_MAX_BYTES = int(os.environ.get('VV_LOG_MAX_BYTES') or 5 * 1024 * 1024)
    VV_LOG_BACKUP_COUNT = int(os.environ.get('VV_LOG_BACKUP_COUNT') or 5)
    
    # VibrationVIEW Settings
    VV_CONNECTION_TIMEOUT = float(os.environ.get('VV_CONNECTION_TIMEOUT') or '10.0')
    VV_RETRY_ATTEMPTS = int(os.environ.get('VV_RETRY_ATTEMPTS') or '5')
    VV_MAX_INSTANCES = int(os.environ.get('VV_MAX_INSTANCES') or '5')

    # VibrationVIEW folders - configurable via environment variables
    VIBRATIONVIEW_FOLDER = os.environ.get('VIBRATIONVIEW_FOLDER') or 'C:\\VibrationVIEW'
    PROFILE_FOLDER = os.environ.get('PROFILE_FOLDER') or os.path.join(VIBRATIONVIEW_FOLDER, 'Profiles')
    INPUTCONFIG_FOLDER = os.environ.get('INPUTCONFIG_FOLDER') or os.path.join(VIBRATIONVIEW_FOLDER, 'InputConfig')
    NEW_TEST_DEFAULTS_FOLDER = os.environ.get('NEW_TEST_DEFAULTS_FOLDER') or os.path.join(VIBRATIONVIEW_FOLDER, 'New Test Defaults')
    REPORT_FOLDER = os.environ.get('REPORT_FOLDER') or os.path.join(VIBRATIONVIEW_FOLDER, 'Reports')
    DATA_FOLDER = os.environ.get('DATA_FOLDER') or os.path.join(VIBRATIONVIEW_FOLDER, 'Data')
    EXE_NAME = os.environ.get('EXE_NAME') or 'C:\\Program Files\\VibrationVIEW 2025\\VibrationVIEW.exe'
    
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
    ALLOW_GET_WRITE = True
    API_KEY = ''  # Disable auth — must be set before create_app() registers the before_request hook

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

