# ============================================================================
# FILE: utils/vv_manager.py (Updated to use app singleton)
# ============================================================================

"""
VibrationVIEW manager — imports the singleton from utils.vv_singleton
"""

import logging
from functools import wraps
from typing import Any, Callable

from utils.vv_singleton import get_vv_instance, reset_vv_instance

logger = logging.getLogger(__name__)


class VibrationVIEWManager:
    """Manager for VibrationVIEW instances using the singleton"""

    @classmethod
    def get_instance(cls) -> Any:
        """Get VibrationVIEW instance from singleton"""
        instance = get_vv_instance()
        if instance is None:
            logger.error("Failed to get VibrationVIEW instance")
            raise Exception("VibrationVIEW instance not available")

        logger.debug("VibrationVIEW instance retrieved")
        return instance

    @classmethod
    def release_instance(cls) -> None:
        """Release the VibrationVIEW instance"""
        try:
            reset_vv_instance()
            logger.info("VibrationVIEW instance released")
        except Exception as e:
            logger.error(f"Error releasing VibrationVIEW instance: {e}")


def with_vibrationview(func: Callable) -> Callable:
    """
    Decorator that provides VibrationVIEW instance to route functions
    Now uses the app singleton for consistent testing
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the VibrationVIEW instance from app singleton
        vv = VibrationVIEWManager.get_instance()

        # If your API requires connection, ensure it's connected
        if hasattr(vv, "is_connected") and not vv.is_connected():
            if hasattr(vv, "connect"):
                vv.connect()

        # Call the decorated function — let exceptions propagate to @handle_errors
        return func(vv, *args, **kwargs)

    return wrapper


def with_vibrationview_safe(func: Callable) -> Callable:
    """
    Decorator with built-in error handling and ready check
    Now uses the app singleton for consistent testing
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        vv = VibrationVIEWManager.get_instance()

        # Ensure connection if needed
        if hasattr(vv, "is_connected") and not vv.is_connected():
            if hasattr(vv, "connect"):
                if not vv.connect():
                    return {"success": False, "error": "Failed to connect to VibrationVIEW", "data": None}

        # Check if VibrationVIEW is ready
        if hasattr(vv, "IsReady") and not vv.IsReady():
            return {"success": False, "error": "VibrationVIEW is not ready", "data": None}

        result = func(vv, *args, **kwargs)

        # Ensure result is in proper format
        if isinstance(result, dict) and "success" in result:
            return result
        else:
            return {"success": True, "data": {"result": result}, "error": None}

    return wrapper
