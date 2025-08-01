# ============================================================================
# FILE: utils/decorators.py (Error Handling Decorators)
# ============================================================================

"""
Decorators for error handling and COM exception management
"""

import functools
import logging
from flask import jsonify
from utils.response_helpers import error_response, com_error_response

logger = logging.getLogger(__name__)

def handle_errors(func):
    """
    Decorator to handle COM errors and general exceptions
    
    Automatically catches and formats COM exceptions and other errors
    into standardized API responses.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
            
        except ImportError as e:
            # VibrationVIEW API not available
            logger.error(f"VibrationVIEW API import error in {func.__name__}: {str(e)}")
            return jsonify(error_response(
                "VibrationVIEW API not available. Ensure vibrationview-api is installed.",
                "API_NOT_AVAILABLE"
            )), 503
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific COM errors
            if "CoInitialize has not been called" in error_msg:
                logger.error(f"COM initialization error in {func.__name__}: {error_msg}")
                return jsonify(error_response(
                    "COM initialization failed. This is a threading issue with VibrationVIEW COM interface.",
                    "COM_INIT_ERROR"
                )), 500
            
            elif "Failed to connect to VibrationVIEW" in error_msg:
                logger.error(f"VibrationVIEW connection error in {func.__name__}: {error_msg}")
                return jsonify(error_response(
                    "Cannot connect to VibrationVIEW. Ensure VibrationVIEW is running and COM interface is available.",
                    "CONNECTION_ERROR"
                )), 503
            
            # Check if it's a COM exception
            elif hasattr(e, 'hresult') or 'com' in str(type(e)).lower():
                logger.error(f"COM error in {func.__name__}: {error_msg}")
                return jsonify(com_error_response(e)), 500
            
            # General exception
            logger.error(f"Error in {func.__name__}: {error_msg}")
            return jsonify(error_response(
                f"Internal server error: {error_msg}",
                "INTERNAL_ERROR"
            )), 500
    
    return wrapper

def require_vv_connection(func):
    """
    Decorator to ensure VibrationVIEW connection is available
    
    Can be used to add connection validation before method execution.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # This could be expanded to pre-validate connection
            return func(*args, **kwargs)
        except Exception as e:
            if "connection" in str(e).lower() or "dispatch" in str(e).lower():
                logger.error(f"VibrationVIEW connection error in {func.__name__}: {str(e)}")
                return jsonify(error_response(
                    "Unable to connect to VibrationVIEW. Ensure VibrationVIEW is running and COM interface is available.",
                    "CONNECTION_ERROR"
                )), 503
            raise
    
    return wrapper