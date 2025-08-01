# ============================================================================
# FILE: utils/vv_manager.py (Updated to use app singleton)
# ============================================================================

"""
VibrationVIEW manager using the app singleton
"""

from functools import wraps
import logging

logger = logging.getLogger(__name__)

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
            # Return error response that matches your API format
            return {
                'success': False,
                'error': str(e),
                'data': None
            }, 500
    
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
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    return wrapper