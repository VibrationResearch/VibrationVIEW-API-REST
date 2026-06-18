# ============================================================================
# FILE: utils/vv_manager.py
# ============================================================================

"""
VibrationVIEW singleton instance management and COM call serialization.

The singleton lives here (not in app.py) to avoid circular imports — route
modules import from this file, and app.py re-exports the public API for
backward compatibility with tests.
"""

import logging
import threading
from functools import wraps

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton state
# ---------------------------------------------------------------------------
_vv_instance = None
_vv_lock = threading.Lock()
_com_lock = threading.Lock()


def create_vv_instance():
    """Create a new VibrationVIEW COM connection.

    Returns the instance on success, or None on failure.
    """
    try:
        from vibrationviewapi import VibrationVIEW

        vv_instance = VibrationVIEW()

        if vv_instance.vv is None:
            logger.error("Failed to connect to VibrationVIEW")
            return None

        logger.info("VibrationVIEW singleton instance created successfully")
        return vv_instance

    except ImportError as e:
        logger.error(f"Could not import VibrationVIEW API: {e}")
        return None
    except Exception as e:
        logger.critical(
            f"Error connecting to VibrationVIEW: {e}. "
            "Possible causes: (1) VibrationVIEW is not running, "
            "(2) the Automation Interface option (VR9604) is not licensed, "
            "(3) the IO box is not connected or powered on."
        )
        return None


def get_vv_instance():
    """Get VibrationVIEW instance — thread-safe singleton with stale detection.

    If the cached instance is stale (VibrationVIEW was restarted or crashed),
    resets the singleton and retries the connection.
    """
    global _vv_instance

    if _vv_instance is not None:
        # Verify the COM object is still alive
        try:
            _vv_instance.vv  # noqa: B018 — access the property to trigger thread-local check
        except Exception:
            logger.warning("VibrationVIEW COM object is stale, reconnecting...")
            reset_vv_instance()
            # Fall through to create a new instance below

    if _vv_instance is not None:
        return _vv_instance

    with _vv_lock:
        # Double-check locking pattern
        if _vv_instance is not None:
            return _vv_instance

        _vv_instance = create_vv_instance()
        return _vv_instance


def set_vv_instance(instance):
    """Set the VibrationVIEW instance — useful for testing."""
    global _vv_instance
    with _vv_lock:
        _vv_instance = instance


def reset_vv_instance():
    """Reset the VibrationVIEW instance — releases COM object and clears singleton."""
    global _vv_instance
    with _vv_lock:
        if _vv_instance is not None:
            try:
                del _vv_instance
                logger.info("VibrationVIEW COM object released")
            except Exception as e:
                logger.error(f"Error releasing VibrationVIEW COM object: {e}")
        _vv_instance = None


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------
def with_vibrationview(func):
    """
    Decorator that provides VibrationVIEW instance to route functions.

    Acquires a module-level lock so that COM calls are serialized even when
    Waitress (or another WSGI server) dispatches requests on multiple threads.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        vv = get_vv_instance()
        if vv is None:
            raise RuntimeError(
                "VibrationVIEW is not connected. "
                "Possible causes: (1) VibrationVIEW is not running, "
                "(2) the Automation Interface option (VR9604) is not licensed, "
                "(3) the IO box is not connected or powered on."
            )

        with _com_lock:
            return func(vv, *args, **kwargs)

    return wrapper
