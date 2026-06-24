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
import time

logger = logging.getLogger(__name__)

# Global singleton instance and lock
_vv_instance = None
_vv_lock = threading.Lock()

# Cooldown after a failed connection to avoid blocking every request
# with the full retry loop in the VibrationVIEW constructor.
_RETRY_COOLDOWN_SECONDS = 30
_last_failure_time = 0.0


def get_vv_instance():
    """Get VibrationVIEW instance - thread-safe singleton"""
    global _vv_instance, _last_failure_time

    if _vv_instance is not None:
        return _vv_instance

    with _vv_lock:
        # Double-check locking pattern
        if _vv_instance is not None:
            return _vv_instance

        # Don't retry if we recently failed — the VibrationVIEW constructor
        # blocks for several seconds on each attempt.
        if _last_failure_time and (time.monotonic() - _last_failure_time) < _RETRY_COOLDOWN_SECONDS:
            return None

        try:
            from vibrationviewapi import VibrationVIEW

            vv_instance = VibrationVIEW()

            _vv_instance = vv_instance
            _last_failure_time = 0.0
            logger.info("VibrationVIEW singleton instance created successfully")
            return _vv_instance

        except ImportError as e:
            logger.error(f"Could not import VibrationVIEW API: {e}")
            return None
        except Exception as e:
            _last_failure_time = time.monotonic()
            logger.error(
                f"Error connecting to VibrationVIEW: {e}. "
                f"Will retry in {_RETRY_COOLDOWN_SECONDS}s. "
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
    global _vv_instance, _last_failure_time
    with _vv_lock:
        _last_failure_time = 0.0
        if _vv_instance is not None:
            try:
                # Delete instance - lets Python/COM release the object
                del _vv_instance
                logger.info("VibrationVIEW COM object released")
            except Exception as e:
                logger.error(f"Error releasing VibrationVIEW COM object: {e}")
        _vv_instance = None
