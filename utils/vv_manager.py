# ============================================================================
# FILE: utils/vv_manager.py (Updated to use app singleton)
# ============================================================================

"""
VibrationVIEW manager using the app singleton
"""

import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)


class VibrationVIEWManager:
    """Manager for VibrationVIEW instances using app singleton"""

    @classmethod
    def get_instance(cls):
        """Get VibrationVIEW instance from app singleton.

        If the cached instance is stale (VibrationVIEW was restarted or
        crashed), resets the singleton and retries the connection.
        """
        from app import get_vv_instance, reset_vv_instance

        instance = get_vv_instance()
        if instance is None:
            raise RuntimeError(
                "VibrationVIEW is not connected. "
                "Possible causes: (1) VibrationVIEW is not running, "
                "(2) the Automation Interface option (VR9604) is not licensed, "
                "(3) the IO box is not connected or powered on."
            )

        # Verify the COM object is still alive
        try:
            instance.vv  # noqa: B018 — access the property to trigger thread-local check
        except Exception:
            logger.warning("VibrationVIEW COM object is stale, reconnecting...")
            reset_vv_instance()
            instance = get_vv_instance()
            if instance is None:
                raise RuntimeError(
                    "VibrationVIEW connection lost and reconnection failed. "
                    "Ensure VibrationVIEW is running."
                )

        return instance

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


_com_lock = threading.Lock()


def with_vibrationview(func):
    """
    Decorator that provides VibrationVIEW instance to route functions.

    Acquires a module-level lock so that COM calls are serialized even when
    Waitress (or another WSGI server) dispatches requests on multiple threads.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        vv = VibrationVIEWManager.get_instance()

        with _com_lock:
            return func(vv, *args, **kwargs)

    return wrapper
