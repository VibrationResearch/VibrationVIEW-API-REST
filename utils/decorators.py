# ============================================================================
# FILE: utils/decorators.py (Error Handling Decorators)
# ============================================================================

"""
Decorators for error handling and COM exception management
"""

import functools
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.response_helpers import com_error_response, error_response
from utils.vv_error_codes import classify_vview_error, get_error_info

logger = logging.getLogger(__name__)


def handle_errors(func):
    """
    Decorator to handle COM errors and general exceptions

    Automatically catches and formats COM exceptions and other errors into standardized API responses.  
	Known VibrationVIEW HRESULT codes are mapped to specific HTTP status codes and error codes - vv_error_codes.classify_vview_error().
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except HTTPException:
            # Re-raise HTTP errors (e.g. 413 Request Entity Too Large) so
            # Flask handles them instead of swallowing them as 500s.
            raise

        except ImportError as e:
            # VibrationVIEW API not available
            logger.error(f"VibrationVIEW API import error in {func.__name__}: {str(e)}")
            return jsonify(
                error_response(
                    "VibrationVIEW API not available. Ensure vibrationview-api is installed.", "API_NOT_AVAILABLE"
                )
            ), 503

        except Exception as e:
            error_msg = str(e)

            # Check for specific COM errors
            if "CoInitialize has not been called" in error_msg:
                logger.error(f"COM initialization error in {func.__name__}: {error_msg}")
                return jsonify(
                    error_response(
                        "COM initialization failed. This is a threading issue with VibrationVIEW COM interface.",
                        "COM_INIT_ERROR",
                    )
                ), 500

            elif "Failed to connect to VibrationVIEW" in error_msg:
                logger.error(f"VibrationVIEW connection error in {func.__name__}: {error_msg}")
                return jsonify(
                    error_response(
                        "Cannot connect to VibrationVIEW. Ensure VibrationVIEW is running and COM interface is available.",
                        "CONNECTION_ERROR",
                    )
                ), 503

            # Check if it's a COM exception with a known VibrationVIEW error code
            error_info = get_error_info(e)
            if error_info:
                http_status, error_code, message = classify_vview_error(error_info["code"])
                logger.error(f"VibrationVIEW error in {func.__name__}: {error_code} - {message}")
                return jsonify(error_response(message, error_code, details=error_info)), http_status

            # Generic COM exception (hresult present but not a known VV code)
            if hasattr(e, "hresult") or "com" in str(type(e)).lower():
                logger.error(f"COM error in {func.__name__}: {error_msg}")
                return jsonify(com_error_response(e)), 500

            # General exception
            logger.error(f"Error in {func.__name__}: {error_msg}")
            return jsonify(error_response(f"Internal server error: {error_msg}", "INTERNAL_ERROR")), 500

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
                return jsonify(
                    error_response(
                        "Unable to connect to VibrationVIEW. Ensure VibrationVIEW is running and COM interface is available.",
                        "CONNECTION_ERROR",
                    )
                ), 503
            raise

    return wrapper
