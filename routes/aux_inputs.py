# ============================================================================
# FILE: routes/aux_inputs.py
# ============================================================================

"""
routes/aux_inputs.py

Auxiliary input properties and metadata methods
- Rear input channel metadata (1-based indexing)
"""

from typing import Any

from flask import Blueprint, Response, jsonify, request

from utils.decorators import handle_errors
from utils.response_helpers import success_response
from utils.utils import convert_channel_to_com_index
from utils.vv_manager import with_vibrationview

auxinputs_bp = Blueprint("auxinputs", __name__, url_prefix="/api")


@auxinputs_bp.route("/docs/auxinputs", methods=["GET"])
def auxinputs_docs() -> Response:
    """Documentation for auxiliary inputs endpoints"""
    docs = {
        "module": "auxinputs",
        "description": "Auxiliary input properties and metadata methods",
        "note": "Channel parameters use 1-based indexing (user-friendly) and are converted to 0-based for VibrationVIEW COM interface",
        "endpoints": {
            "Rear Input Data": {
                "GET /rearinput": "RearInput() -> List[float] - Get rear input values for all channels"
            },
            "Rear Input Metadata": {
                "GET /rearinputunit?channel=<int>": "RearInputUnit(channel: int) -> str - Get rear input units (1-based)",
                "GET /rearinputunit?<int>": "RearInputUnit(channel: int) -> str - Get rear input units using unnamed parameter (1-based)",
                "GET /rearinputlabel?channel=<int>": "RearInputLabel(channel: int) -> str - Get rear input label (1-based)",
                "GET /rearinputlabel?<int>": "RearInputLabel(channel: int) -> str - Get rear input label using unnamed parameter (1-based)",
            },
        },
        "parameter_notes": {
            "channel_indexing": "Channel parameters use 1-based indexing",
            "conversion": "API automatically converts 1-based user input to 0-based VibrationVIEW COM interface",
            "validation": "Channel numbers must be >= 1, will return error for channel 0 or negative values",
        },
    }
    return jsonify(docs)


@auxinputs_bp.route("/rearinput", methods=["GET"])
@handle_errors
@with_vibrationview
def rear_input(vv_instance: Any) -> Response:
    """
    Get Rear Input Values for All Channels

    COM Method: RearInput()
    Returns the rear input values for all auxiliary input channels.
    Array returned in order: [channel1, channel2, channel3, ...] (1-based channel numbering for reference)
    """
    result = vv_instance.RearInput()

    return jsonify(success_response({"result": result}, f"Retrieved {len(result)} rear input values"))


@auxinputs_bp.route("/rearinputunit", methods=["GET"])
@handle_errors
@with_vibrationview
def rear_input_unit(vv_instance: Any) -> Response | tuple[Response, int]:
    """Get units for the rear input channel (1-based indexing)"""
    # Get channel from 'channel' parameter or first unnamed parameter
    channel_raw = request.args.get("channel")
    if channel_raw is None:
        args = list(request.args.keys())
        if args:
            channel_raw = args[0]

    if channel_raw is None:
        return jsonify(
            {"success": False, "error": "Missing required parameter: channel (or unnamed numeric parameter)"}
        ), 400

    channel_com, err, status = convert_channel_to_com_index(channel_raw)
    if err:
        return jsonify(err), status

    result = vv_instance.RearInputUnit(channel_com)

    return jsonify(success_response({"result": result, "channel": int(channel_raw), "internal_channel": channel_com}))


@auxinputs_bp.route("/rearinputlabel", methods=["GET"])
@handle_errors
@with_vibrationview
def rear_input_label(vv_instance: Any) -> Response | tuple[Response, int]:
    """Get label for the rear input channel (1-based indexing)"""
    # Get channel from 'channel' parameter or first unnamed parameter
    channel_raw = request.args.get("channel")
    if channel_raw is None:
        args = list(request.args.keys())
        if args:
            channel_raw = args[0]

    if channel_raw is None:
        return jsonify(
            {"success": False, "error": "Missing required parameter: channel (or unnamed numeric parameter)"}
        ), 400

    channel_com, err, status = convert_channel_to_com_index(channel_raw)
    if err:
        return jsonify(err), status

    result = vv_instance.RearInputLabel(channel_com)

    return jsonify(success_response({"result": result, "channel": int(channel_raw), "internal_channel": channel_com}))
