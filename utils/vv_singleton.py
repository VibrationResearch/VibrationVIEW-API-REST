# ============================================================================
# FILE: utils/vv_singleton.py (VibrationVIEW Instance Management)
# ============================================================================

"""
Global VibrationVIEW COM instance.

This module owns the single VibrationVIEW connection shared across the
application.  Both app.py and utils/vv_manager.py import from here,
avoiding the circular-import situation that previously required deferred
imports inside function bodies.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# Global instance and creation lock
_vv_instance = None
_vv_lock = threading.Lock()


def get_vv_instance():
    """Return the VibrationVIEW instance, creating it on first call."""
    global _vv_instance

    if _vv_instance is None:
        with _vv_lock:
            if _vv_instance is None:
                try:
                    from vibrationviewapi import VibrationVIEW

                    _vv_instance = VibrationVIEW()
                    logger.info("VibrationVIEW instance created successfully")
                except ImportError as e:
                    logger.error(f"Could not import VibrationVIEW API: {e}")
                    return None
                except Exception as e:
                    logger.error(
                        f"Error connecting to VibrationVIEW: {e}. "
                        "Verify VibrationVIEW is running and the Automation Interface option (VR9604) is licensed."
                    )
                    return None

    inst = _vv_instance
    if inst is None or not inst.IsReady():
        logger.info("VibrationVIEW hardware not ready - check if the controller is connected and powered on")
        return None

    return inst


def set_vv_instance(instance):
    """Set the VibrationVIEW instance - useful for testing"""
    global _vv_instance
    with _vv_lock:
        _vv_instance = instance


def reset_vv_instance():
    """Reset the VibrationVIEW instance - releases COM object and clears singleton"""
    global _vv_instance
    with _vv_lock:
        if _vv_instance is not None:
            try:
                _vv_instance.close()
                logger.info("VibrationVIEW COM object released")
            except Exception as e:
                logger.error(f"Error releasing VibrationVIEW COM object: {e}")
        _vv_instance = None
