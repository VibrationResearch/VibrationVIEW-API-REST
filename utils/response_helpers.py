# ============================================================================
# FILE: utils/response_helpers.py (Response Formatting Utilities)
# ============================================================================

"""
Response formatting utilities for consistent API responses
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def success_response(data: Any = None, message: str = "Operation completed successfully") -> Dict:
    """
    Create standardized success response

    Args:
        data: Response data payload
        message: Success message

    Returns:
        Dict: Standardized success response
    """
    response = {"success": True, "message": message, "timestamp": datetime.now(timezone.utc).isoformat()}

    if data is not None:
        response["data"] = data

    return response


def error_response(message: str, error_code: str = "GENERIC_ERROR", details: Optional[Dict] = None) -> Dict:
    """
    Create standardized error response

    Args:
        message: Error message
        error_code: Error code identifier
        details: Additional error details

    Returns:
        Dict: Standardized error response
    """
    error: Dict[str, Any] = {"code": error_code, "message": message}

    if details:
        error["details"] = details

    response: Dict[str, Any] = {
        "success": False,
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return response


def com_error_response(com_exception: Exception) -> Dict:
    """
    Create standardized COM error response

    Args:
        com_exception: COM exception object

    Returns:
        Dict: Standardized COM error response
    """
    from utils.vv_error_codes import get_error_info

    details: Dict[str, Any] = {
        "exception_type": type(com_exception).__name__,
        "com_hresult": getattr(com_exception, "hresult", None),
    }

    error_info = get_error_info(com_exception)
    if error_info:
        details["vv_error"] = error_info

    return error_response(
        message=f"VibrationVIEW COM Error: {str(com_exception)}", error_code="COM_ERROR", details=details
    )
