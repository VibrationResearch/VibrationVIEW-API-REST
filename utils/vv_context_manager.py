# ============================================================================
# FILE: utils/vv_context_manager.py (VibrationVIEW Context Manager)
# ============================================================================

"""
Context manager wrapper for VibrationVIEW API using the official thread-safe implementation
"""

import logging
from vibrationviewapi import VibrationVIEW

logger = logging.getLogger(__name__)

def get_vibrationview():
    """
    Factory function to create VibrationVIEW context manager using the official implementation
    
    Usage:
        with get_vibrationview() as vv:
            result = vv.StartTest()
    """
    return VibrationVIEW()

# For backwards compatibility, keep the old interface
class VibrationVIEWWrapper:
    """Simple wrapper around the official VibrationVIEWContext"""
    
    def __enter__(self):
        self.context = VibrationVIEW()
        self.vv = self.context.__enter__()
        logger.debug("VibrationVIEW connection established via official context manager")
        return self.vv
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        result = self.context.__exit__(exc_type, exc_val, exc_tb)
        logger.debug("VibrationVIEW connection closed via official context manager")
        return result