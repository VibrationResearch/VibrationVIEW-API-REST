# ============================================================================
# FILE: routes/advanced_control.py (Test Control Routes) - Updated for URL Parameters
# ============================================================================

"""
Test Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Advanced test control operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging

# Create blueprint
advanced_control_bp = Blueprint("advanced_control", __name__)

logger = logging.getLogger(__name__)


@advanced_control_bp.route("/docs/advanced_control", methods=["GET"])
def get_documentation():
    """Get test control module documentation"""
    docs = {
        "module": "advanced_control",
        "description": "1:1 mapping of VibrationVIEW COM advanced test control methods",
        "com_object": "VibrationVIEW.Application",
        "endpoints": {
            "Parameter Control (Get/Set)": {
                "GET|POST /testtype": {
                    "description": "Get/Set test type",
                    "com_method": "TestType() or TestType(value)",
                    "parameters": {
                        "value": "int - Test type value (POST URL parameter only)"
                    },
                    "returns": "int - Current test type",
                    "example": "POST /api/testtype?value=1",
                },
            }
        },
        "notes": [
            "GET requests return current parameter value",
            'POST requests with "value" URL parameter set parameter and return new value',
            "All POST parameter setting uses URL parameters, not JSON body",
            "COM interface uses 0-based indexing for all arrays",
        ],
    }
    return jsonify(docs)


# Parameter Control (Get/Set) - Updated to use URL parameters
@advanced_control_bp.route("/testtype", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def test_type(vv_instance):
    """
    Get/Set Test Type

    COM Method: TestType() or TestType(value)
    Controls the current test type.

    GET: Returns current test type
    POST: Sets test type from URL parameter 'value'

    Example: POST /api/testtype?value=1
    """
    if request.method == "GET":
        result = vv_instance.TestType()
        return jsonify(
            success_response({"result": result}, f"TestType retrieved: {result}")
        )
    else:
        value = request.args.get("value", type=int)
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.TestType(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"TestType set to {value}, returned: {result}",
            )
        )
