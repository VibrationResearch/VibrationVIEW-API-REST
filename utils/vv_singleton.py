# ============================================================================
# FILE: utils/vv_singleton.py (VibrationVIEW Singleton Management)
# ============================================================================

"""
Thread-safe singleton for the VibrationVIEW COM instance.

This module owns the single VibrationVIEW connection shared across the
application.  Both app.py and utils/vv_manager.py import from here,
avoiding the circular-import situation that previously required deferred
imports inside function bodies.
"""

import logging
import threading

logger = logging.getLogger(__name__)

# Global singleton instance and lock
_vv_instance = None
_vv_lock = threading.Lock()

def get_vv_instance():
    """Get VibrationVIEW instance - thread-safe singleton"""
    global _vv_instance

    if _vv_instance is not None:
        return _vv_instance

    with _vv_lock:
        # Double-check locking pattern
        if _vv_instance is not None:
            return _vv_instance

        try:
            from vibrationviewapi import VibrationVIEW

            vv_instance = VibrationVIEW()

            _vv_instance = vv_instance
            logger.info("VibrationVIEW singleton instance created successfully")
            return _vv_instance

        except ImportError as e:
            logger.error(f"Could not import VibrationVIEW API: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Error connecting to VibrationVIEW: {e}. "
                "Verify VibrationVIEW is running and the Automation Interface option (VR9604) is licensed."
            )
            return None


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
                # Delete instance - lets Python/COM release the object
                del _vv_instance
                logger.info("VibrationVIEW COM object released")
            except Exception as e:
                logger.error(f"Error releasing VibrationVIEW COM object: {e}")
        _vv_instance = None
