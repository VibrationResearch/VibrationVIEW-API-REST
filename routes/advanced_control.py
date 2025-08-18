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


@advanced_control_bp.route("/systemcheckfrequency", methods=["GET", "POST"])
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


@advanced_control_bp.route("/systemcheckoutputvoltage", methods=["GET", "POST"])
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
