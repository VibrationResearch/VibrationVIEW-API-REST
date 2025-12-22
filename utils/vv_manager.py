# ============================================================================
# FILE: utils/vv_manager.py (Updated to use app singleton)
# ============================================================================

"""
VibrationVIEW manager using the app singleton
"""

from functools import wraps
import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def extract_exception_info(e):
    """Extract detailed information from an exception for JSON response"""
    error_info = {
        'raw': str(e),
        'type': type(e).__name__
    }

    # Try to extract COM error details
    if hasattr(e, 'args') and e.args:
        args = e.args
        if isinstance(args, tuple) and len(args) >= 3:
            # COM errors often have (hr, description, exc, argErr) format
            error_info['hr'] = args[0] if len(args) > 0 else None
            error_info['description'] = args[1] if len(args) > 1 else None
            if len(args) > 2 and args[2]:
                exc_info = args[2]
                if isinstance(exc_info, tuple):
                    error_info['source'] = exc_info[1] if len(exc_info) > 1 else None
                    error_info['details'] = exc_info[2] if len(exc_info) > 2 else None
                    error_info['help_file'] = exc_info[3] if len(exc_info) > 3 else None
                    error_info['help_context'] = exc_info[4] if len(exc_info) > 4 else None
                    error_info['scode'] = exc_info[5] if len(exc_info) > 5 else None

    # Clean up None values
    return {k: v for k, v in error_info.items() if v is not None}

class VibrationVIEWManager:
    """Manager for VibrationVIEW instances using app singleton"""
    
    @classmethod
    def get_instance(cls):
        """Get VibrationVIEW instance from app singleton"""
        try:
            # Import here to avoid circular imports
            from app import get_vv_instance
            
            instance = get_vv_instance()
            if instance is None:
                logger.error("Failed to get VibrationVIEW instance from app singleton")
                raise Exception("VibrationVIEW instance not available")
            
            logger.debug("VibrationVIEW instance retrieved from app singleton")
            return instance
            
        except ImportError as e:
            logger.error(f"Failed to import get_vv_instance from app: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to get VibrationVIEW instance: {e}")
            raise
    
    @classmethod
    def release_instance(cls):
        """Release the VibrationVIEW instance"""
        try:
            # Import here to avoid circular imports
            from app import reset_vv_instance
            reset_vv_instance()
            logger.info("VibrationVIEW instance released via app singleton")
        except ImportError:
            logger.warning("Could not import reset_vv_instance from app")
        except Exception as e:
            logger.error(f"Error releasing VibrationVIEW instance: {e}")

def with_vibrationview(func):
    """
    Decorator that provides VibrationVIEW instance to route functions
    Now uses the app singleton for consistent testing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get the VibrationVIEW instance from app singleton
            vv = VibrationVIEWManager.get_instance()
            
            # If your API requires connection, ensure it's connected
            if hasattr(vv, 'is_connected') and not vv.is_connected():
                if hasattr(vv, 'connect'):
                    vv.connect()
            
            # Call the decorated function with the VibrationVIEW instance as first parameter
            return func(vv, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in VibrationVIEW operation: {e}")
            # Return detailed error response
            error_info = extract_exception_info(e)
            return jsonify({
                'success': False,
                'error': error_info,
                'data': None
            }), 500

    return wrapper

def with_vibrationview_safe(func):
    """
    Decorator with built-in error handling and ready check
    Now uses the app singleton for consistent testing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            vv = VibrationVIEWManager.get_instance()
            
            # Ensure connection if needed
            if hasattr(vv, 'is_connected') and not vv.is_connected():
                if hasattr(vv, 'connect'):
                    if not vv.connect():
                        return {
                            'success': False,
                            'error': 'Failed to connect to VibrationVIEW',
                            'data': None
                        }
            
            # Check if VibrationVIEW is ready
            if hasattr(vv, 'IsReady') and not vv.IsReady():
                return {
                    'success': False,
                    'error': 'VibrationVIEW is not ready',
                    'data': None
                }
            
            result = func(vv, *args, **kwargs)
            
            # Ensure result is in proper format
            if isinstance(result, dict) and 'success' in result:
                return result
            else:
                return {
                    'success': True,
                    'data': {'result': result},
                    'error': None
                }
                
        except Exception as e:
            logger.error(f"VibrationVIEW operation failed: {e}")
            error_info = extract_exception_info(e)
            return jsonify({
                'success': False,
                'error': error_info,
                'data': None
            }), 500

    return wrapper