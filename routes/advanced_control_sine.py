# ============================================================================
# FILE: routes/advanced_control_sine.py (Sine Advanced Control Routes)
# ============================================================================

"""
Sine Advanced Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Sine-specific advanced test control operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging

# Create blueprint
advanced_control_sine_bp = Blueprint("advanced_control_sine", __name__)

logger = logging.getLogger(__name__)


@advanced_control_sine_bp.route("/docs/advanced_control_sine", methods=["GET"])
def get_documentation():
    """Get sine advanced control module documentation"""
    docs = {
        "module": "advanced_control_sine",
        "description": (
            "1:1 mapping of VibrationVIEW COM sine-specific advanced control methods"
        ),
        "com_object": "VibrationVIEW.Application",
        "endpoints": {
            "Sine Sweep Control": {
                "POST /sweepup": {
                    "description": "Sine sweep up",
                    "com_method": "SweepUp()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
                "POST /sweepdown": {
                    "description": "Sine sweep down",
                    "com_method": "SweepDown()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
                "POST /sweepstepup": {
                    "description": "Step up to next integer frequency",
                    "com_method": "SweepStepUp()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
                "POST /sweepstepdown": {
                    "description": "Step down to next integer frequency",
                    "com_method": "SweepStepDown()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
                "POST /sweephold": {
                    "description": "Hold sweep frequency",
                    "com_method": "SweepHold()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
                "POST /sweepresonancehold": {
                    "description": "Hold resonance",
                    "com_method": "SweepResonanceHold()",
                    "parameters": "None",
                    "returns": "boolean - Success status from COM method",
                },
            },
            "Sine Parameter Control (Get/Set)": {
                "GET|POST /demandmultiplier": {
                    "description": "Get/Set demand output multiplier (dB)",
                    "com_method": "DemandMultiplier() or DemandMultiplier(value)",
                    "parameters": {
                        "value": (
                            "float - Multiplier value in dB (POST URL parameter only)"
                        )
                    },
                    "returns": "float - Current multiplier value",
                    "example": "POST /api/demandmultiplier?value=6.0 or /api/demandmultiplier?6.0",
                },
                "GET|POST /sweepmultiplier": {
                    "description": "Get/Set sine sweep multiplier (linear)",
                    "com_method": "SweepMultiplier() or SweepMultiplier(value)",
                    "parameters": {
                        "value": "float - Multiplier value (POST URL parameter only)"
                    },
                    "returns": "float - Current multiplier value",
                    "example": "POST /api/sweepmultiplier?value=1.5 or /api/sweepmultiplier?1.5",
                },
                "GET|POST /sinefrequency": {
                    "description": "Get/Set sine frequency",
                    "com_method": "SineFrequency() or SineFrequency(value)",
                    "parameters": {
                        "value": "float - Frequency value (POST URL parameter only)"
                    },
                    "returns": "float - Current frequency",
                    "example": "POST /api/sinefrequency?value=100.0 or /api/sinefrequency?30",
                },
            },
        },
        "notes": [
            "All sweep methods work specifically with sine test types",
            "These methods control sweep behavior during active sine tests",
            "GET requests return current parameter value",
            (
                'POST requests with "value" URL parameter set parameter and '
                "return new value"
            ),
            "COM interface uses 0-based indexing for all arrays",
        ],
    }
    return jsonify(docs)


# Sine Sweep Control Methods
@advanced_control_sine_bp.route("/sweepup", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_up(vv_instance):
    """
    Sine Sweep Up

    COM Method: SweepUp()
    Increases the frequency during a sine sweep test.
    """
    vv_instance.SweepUp()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepUp command {'executed successfully' if result else 'failed'}",
        )
    )


@advanced_control_sine_bp.route("/sweepdown", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_down(vv_instance):
    """
    Sine Sweep Down

    COM Method: SweepDown()
    Decreases the frequency during a sine sweep test.
    """
    vv_instance.SweepDown()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepDown command {'executed successfully' if result else 'failed'}",
        )
    )


@advanced_control_sine_bp.route("/sweepstepup", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_step_up(vv_instance):
    """
    Sine Sweep Step Up

    COM Method: SweepStepUp()
    Steps up to the next integer frequency during a sine sweep.
    """
    vv_instance.SweepStepUp()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepStepUp command {'executed successfully' if result else 'failed'}",
        )
    )


@advanced_control_sine_bp.route("/sweepstepdown", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_step_down(vv_instance):
    """
    Sine Sweep Step Down

    COM Method: SweepStepDown()
    Steps down to the next integer frequency during a sine sweep.
    """
    vv_instance.SweepStepDown()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepStepDown command {'executed successfully' if result else 'failed'}",
        )
    )


@advanced_control_sine_bp.route("/sweephold", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_hold(vv_instance):
    """
    Sine Hold Sweep Frequency

    COM Method: SweepHold()
    Holds the current sweep frequency during a sine sweep test.
    """
    vv_instance.SweepHold()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepHold command {'executed successfully' if result else 'failed'}",
        )
    )


@advanced_control_sine_bp.route("/sweepresonancehold", methods=["POST"])
@handle_errors
@with_vibrationview
def sweep_resonance_hold(vv_instance):
    """
    Sine Hold Resonance

    COM Method: SweepResonanceHold()
    Holds at the resonance frequency during a sine sweep test.
    """
    vv_instance.SweepResonanceHold()
    result = True

    return jsonify(
        success_response(
            {"result": result, "executed": True},
            f"SweepResonanceHold command {'executed successfully' if result else 'failed'}",
        )
    )


# Sine Parameter Control (Get/Set) Methods
@advanced_control_sine_bp.route("/demandmultiplier", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def demand_multiplier(vv_instance):
    """
    Get/Set Demand Output Multiplier

    COM Method: DemandMultiplier() or DemandMultiplier(value)
    Controls the multiplier for demand output in dB.

    GET: Returns current multiplier value
    POST: Sets multiplier value from URL parameter 'value' or unnamed parameter

    Example: POST /api/demandmultiplier?value=6.0 or POST /api/demandmultiplier?6.0
    """
    if request.method == "GET":
        result = vv_instance.DemandMultiplier()
        return jsonify(
            success_response(
                {"result": result}, f"DemandMultiplier retrieved: {result} dB"
            )
        )
    else:
        value = request.args.get("value", type=float)
        
        # If no 'value' parameter, try to get the first unnamed parameter
        if value is None:
            args = list(request.args.keys())
            if args and args[0].replace('.', '').replace('-', '').isdigit():
                try:
                    value = float(args[0])
                except ValueError:
                    pass
        
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value (or unnamed numeric parameter)", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.DemandMultiplier(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"DemandMultiplier set to {value} dB, returned: {result} dB",
            )
        )


@advanced_control_sine_bp.route("/sweepmultiplier", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def sweep_multiplier(vv_instance):
    """
    Get/Set Sine Sweep Multiplier

    COM Method: SweepMultiplier() or SweepMultiplier(value)
    Controls the multiplier for sine sweep (linear scale).

    GET: Returns current multiplier value
    POST: Sets multiplier value from URL parameter 'value' or unnamed parameter

    Example: POST /api/sweepmultiplier?value=1.5 or POST /api/sweepmultiplier?1.5
    """
    if request.method == "GET":
        result = vv_instance.SweepMultiplier()
        return jsonify(
            success_response({"result": result}, f"SweepMultiplier retrieved: {result}")
        )
    else:
        value = request.args.get("value", type=float)
        
        # If no 'value' parameter, try to get the first unnamed parameter
        if value is None:
            args = list(request.args.keys())
            if args and args[0].replace('.', '').replace('-', '').isdigit():
                try:
                    value = float(args[0])
                except ValueError:
                    pass
        
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value (or unnamed numeric parameter)", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.SweepMultiplier(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"SweepMultiplier set to {value}, returned: {result}",
            )
        )


@advanced_control_sine_bp.route("/sinefrequency", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def sine_frequency(vv_instance):
    """
    Get/Set Sine Frequency

    COM Method: SineFrequency() or SineFrequency(value)
    Controls the sine test frequency.

    GET: Returns current frequency
    POST: Sets frequency from URL parameter 'value' or unnamed parameter

    Example: POST /api/sinefrequency?value=100.0 or POST /api/sinefrequency?30
    """
    if request.method == "GET":
        result = vv_instance.SineFrequency()
        return jsonify(
            success_response(
                {"result": result}, f"SineFrequency retrieved: {result} Hz"
            )
        )
    else:
        value = request.args.get("value", type=float)
        
        # If no 'value' parameter, try to get the first unnamed parameter
        if value is None:
            args = list(request.args.keys())
            if args and args[0].replace('.', '').replace('-', '').isdigit():
                try:
                    value = float(args[0])
                except ValueError:
                    pass
        
        if value is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: value (or unnamed numeric parameter)", "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        result = vv_instance.SineFrequency(value)
        return jsonify(
            success_response(
                {"result": result, "value_set": value},
                f"SineFrequency set to {value} Hz, returned: {result} Hz",
            )
        )
