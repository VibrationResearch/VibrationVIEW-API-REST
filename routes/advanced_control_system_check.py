# ============================================================================
# FILE: routes/advanced_control_system_check.py (System Check Routes)
# ============================================================================

"""
System Check Routes - 1:1 VibrationVIEW COM Interface Mapping
System check operations for frequency and output voltage control
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging

# Create blueprint
advanced_control_system_check_bp = Blueprint("advanced_control_system_check", __name__)

logger = logging.getLogger(__name__)


@advanced_control_system_check_bp.route("/docs/advanced_control_system_check", methods=["GET"])
def get_docs():
    """Documentation for System Check Routes"""
    return jsonify({
        "module": "advanced_control_system_check",
        "description": "System check operations for frequency and output voltage control",
        "endpoints": {
            "GET /docs/advanced_control_system_check": {
                "description": "Get documentation for this module",
                "returns": "dict - This documentation",
            },
            "GET|POST /systemcheckfrequency": {
                "description": "Get/Set system check frequency",
                "com_method": (
                    "SystemCheckFrequency() or SystemCheckFrequency(value)"
                ),
                "parameters": {
                    "value": "float - Frequency value (POST URL parameter only)"
                },
                "returns": "float - Current frequency",
                "example": "POST /api/systemcheckfrequency?value=50.0",
            },
            "GET|POST /systemcheckoutputvoltage": {
                "description": "Get/Set system check output level",
                "com_method": (
                    "SystemCheckOutputVoltage() or SystemCheckOutputVoltage(value)"
                ),
                "parameters": {
                    "value": "float - Voltage value (POST URL parameter only)"
                },
                "returns": "float - Current voltage",
                "example": "POST /api/systemcheckoutputvoltage?value=5.0",
            },
        },
        "notes": [
            "GET requests return current parameter value",
            'POST requests with "value" URL parameter set parameter and return new value',
            "All POST parameter setting uses URL parameters, not JSON body",
            "COM interface uses 0-based indexing for all arrays",
        ],
    })


@advanced_control_system_check_bp.route("/systemcheckfrequency", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def system_check_frequency(vv_instance):
    """
    Get/Set System Check Frequency

    COM Method: SystemCheckFrequency() or SystemCheckFrequency(value)
    Controls the system check frequency.

    GET: Returns current frequency
    POST: Sets frequency from URL parameter 'value'

    Example: POST /api/systemcheckfrequency?value=50.0
    """
    if request.method == "GET":
        result = vv_instance.SystemCheckFrequency()
        return jsonify(
            success_response(
                {"result": result}, f"SystemCheckFrequency retrieved: {result} Hz"
            )
        )
    else:
        value = request.args.get("value", type=float)
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.SystemCheckFrequency(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"SystemCheckFrequency set to {value} Hz, returned: {result} Hz",
            )
        )


@advanced_control_system_check_bp.route("/systemcheckoutputvoltage", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def system_check_output_voltage(vv_instance):
    """
    Get/Set System Check Output Voltage

    COM Method: SystemCheckOutputVoltage() or SystemCheckOutputVoltage(value)
    Controls the system check output level.

    GET: Returns current voltage
    POST: Sets voltage from URL parameter 'value'

    Example: POST /api/systemcheckoutputvoltage?value=5.0
    """
    if request.method == "GET":
        result = vv_instance.SystemCheckOutputVoltage()
        return jsonify(
            success_response(
                {"result": result}, f"SystemCheckOutputVoltage retrieved: {result} V"
            )
        )
    else:
        value = request.args.get("value", type=float)
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.SystemCheckOutputVoltage(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"SystemCheckOutputVoltage set to {value} V, returned: {result} V",
            )
        )