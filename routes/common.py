# ============================================================================
# FILE: routes/common.py (Shared Utilities)
# ============================================================================

"""
routes/common.py

Shared utilities and decorators for all route modules.
"""

import traceback
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import wraps
from flask import jsonify

logger = logging.getLogger(__name__)

def handle_errors(f):
    """Decorator to handle exceptions and return proper JSON responses"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    return wrapper

def success_response(data: Any = None, message: str = "Operation successful") -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if data is not None:
        response['data'] = data
    return response

def validate_required_params(data: dict, required_params: list) -> Optional[str]:
    """Validate that required parameters are present in request data"""
    if not data:
        return "Request body is required"
    
    missing = [param for param in required_params if param not in data]
    if missing:
        return f"Missing required parameters: {', '.join(missing)}"
    return None

def validate_param_types(data: dict, param_types: dict) -> Optional[str]:
    """Validate parameter types"""
    for param, expected_type in param_types.items():
        if param in data and not isinstance(data[param], expected_type):
            return f"Parameter '{param}' must be of type {expected_type.__name__}"
    return None

# ============================================================================
# FILE: .env.example (Environment Variables Template)
# ============================================================================

"""
# VibrationVIEW API Environment Variables
# Copy this file to .env and modify values as needed

# API Configuration
API_VERSION=1.0.0
SECRET_KEY=your-secret-key-here

# CORS Configuration
CORS_ORIGINS=*

# Logging Configuration
LOG_LEVEL=INFO

# VibrationVIEW Configuration
VV_CONNECTION_TIMEOUT=10.0
VV_RETRY_ATTEMPTS=5
VV_MAX_INSTANCES=5

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
"""

