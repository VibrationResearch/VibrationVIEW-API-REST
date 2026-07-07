# ============================================================================
# FILE: routes/data_retrieval.py (Data Retrieval Routes)
# ============================================================================

"""
Data Retrieval Routes - 1:1 VibrationVIEW COM Interface Mapping
Real-time data access operations matching exact COM method signatures
Channel and loop parameters use 1-based indexing (user-friendly)

Includes:
- Primary data arrays (demand, control, channel, output)
- Channel and control metadata
- Raw data file retrieval

Note: Vector data retrieval has been moved to vectors_legacy.py
      Vector methods are superseded by ReportVector in VibrationVIEW 2025.3 and later.
"""

import logging
import os
from typing import Any

from flask import Blueprint, Response, jsonify, request, send_file

from utils.decorators import handle_errors
from utils.exceptions import APIError
from utils.path_validator import PathValidationError, validate_file_path
from utils.response_helpers import success_response
from utils.utils import convert_channel_to_com_index, get_last_data_file
from utils.vv_manager import with_vibrationview

# Create blueprint
data_retrieval_bp = Blueprint("data_retrieval", __name__)

logger = logging.getLogger(__name__)

# ============================================================================
# DOCUMENTATION ENDPOINTS
# ============================================================================


@data_retrieval_bp.route("/docs/data_retrieval", methods=["GET"])
def get_documentation() -> Response:
    """Get data retrieval module documentation"""
    docs = {
        "module": "data_retrieval",
        "description": "1:1 mapping of VibrationVIEW COM data retrieval methods",
        "com_object": "VibrationVIEW.Application",
        "endpoints": {
            "Primary Data Arrays": {
                "GET /demand": {
                    "description": "Get demand values for all loops",
                    "com_method": "Demand()",
                    "parameters": "None",
                    "returns": "List[float] - Demand values for each output loop",
                },
                "GET /control": {
                    "description": "Get control values for all loops",
                    "com_method": "Control()",
                    "parameters": "None",
                    "returns": "List[float] - Control values for each output loop",
                },
                "GET /channel": {
                    "description": "Get channel values for all channels",
                    "com_method": "Channel()",
                    "parameters": "None",
                    "returns": "List[float] - Channel values for all input channels",
                },
                "GET /output": {
                    "description": "Get output values for all loops",
                    "com_method": "Output()",
                    "parameters": "None",
                    "returns": "List[float] - Output values for each output loop",
                },
            },
            "Channel Metadata (1-based indexing)": {
                "GET /channelunit": {
                    "description": "Get channel units",
                    "com_method": "ChannelUnit(channelnum - 1)",
                    "parameters": {
                        "channelnum": "integer - Channel number (1-based, converted to 0-based internally, query parameter)"
                    },
                    "returns": "str - Units for the channel",
                    "example": "GET /api/v1/channelunit?channelnum=3",
                },
                "GET /channellabel": {
                    "description": "Get channel label",
                    "com_method": "ChannelLabel(channelnum - 1)",
                    "parameters": {
                        "channelnum": "integer - Channel number (1-based, converted to 0-based internally, query parameter)"
                    },
                    "returns": "str - Label for the channel",
                    "example": "GET /api/v1/channellabel?channelnum=1",
                },
            },
            "Control Metadata (1-based indexing)": {
                "GET /controlunit": {
                    "description": "Get control loop units",
                    "com_method": "ControlUnit(loopnum - 1)",
                    "parameters": {
                        "loopnum": "integer - Loop number (1-based, converted to 0-based internally, query parameter, defaults to 1)"
                    },
                    "returns": "str - Units for the control loop",
                    "example": "GET /api/v1/controlunit (defaults to loop 1) or GET /api/v1/controlunit?loopnum=2",
                },
                "GET /controllabel": {
                    "description": "Get control loop label",
                    "com_method": "ControlLabel(loopnum - 1)",
                    "parameters": {
                        "loopnum": "integer - Loop number (1-based, converted to 0-based internally, query parameter, defaults to 1)"
                    },
                    "returns": "str - Label for the control loop",
                    "example": "GET /api/v1/controllabel (defaults to loop 1) or GET /api/v1/controllabel?loopnum=2",
                },
            },
        },
        "indexing_notes": {
            "channel_parameters": "Channel and loop parameters use 1-based indexing for user convenience",
            "internal_conversion": "API automatically converts 1-based input to 0-based for VibrationVIEW COM interface",
            "validation": "Channel/loop numbers must be >= 1, will return error for 0 or negative values",
        },
        "notes": [
            "All methods return real-time data from VibrationVIEW",
            "Array sizes depend on hardware configuration",
            "Channel arrays based on input channel count",
            "Control/Demand/Output arrays based on output loop count",
            "Channel and loop parameters use 1-based indexing and are converted internally",
        ],
    }
    return jsonify(docs)


# ============================================================================
# PRIMARY DATA ARRAYS
# ============================================================================


@data_retrieval_bp.route("/demand", methods=["GET"])
@handle_errors
@with_vibrationview
def demand(vv_instance: Any) -> Response:
    """
    Get demand values for all loops

    COM Method: Demand()
    Returns the demand values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Demand()

    return jsonify(success_response({"result": result}, f"Retrieved {len(result)} demand values"))


@data_retrieval_bp.route("/control", methods=["GET"])
@handle_errors
@with_vibrationview
def control(vv_instance: Any) -> Response:
    """
    Get control values for all loops

    COM Method: Control()
    Returns the control values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Control()

    return jsonify(success_response({"result": result}, f"Retrieved {len(result)} control values"))


@data_retrieval_bp.route("/channel", methods=["GET"])
@handle_errors
@with_vibrationview
def channel(vv_instance: Any) -> Response:
    """
    Get channel values for all channels

    COM Method: Channel()
    Returns the channel values for all input channels.
    Array returned in order: [channel1, channel2, channel3, ...] (1-based channel numbering for reference)
    """
    # Note: library wrapper suppresses COM exceptions and returns [] on failure
    result = vv_instance.Channel()

    return jsonify(success_response({"result": result}, f"Retrieved {len(result)} channel values"))


@data_retrieval_bp.route("/output", methods=["GET"])
@handle_errors
@with_vibrationview
def output(vv_instance: Any) -> Response:
    """
    Get output values for all loops

    COM Method: Output()
    Returns the output values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Output()

    return jsonify(success_response({"result": result}, f"Retrieved {len(result)} output values"))


# ============================================================================
# CHANNEL METADATA (1-based indexing with conversion)
# ============================================================================


@data_retrieval_bp.route("/channelunit", methods=["GET"])
@handle_errors
@with_vibrationview
def channel_unit(vv_instance: Any) -> Response:
    """
    Get the channel unit associated with channel number (1-based)

    COM Method: ChannelUnit(channelnum - 1)
    Channel numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.

    Query Parameters:
        channelnum (no parameter name required)

    Example:
        GET /api/v1/channelunit?3
    """
    # Get channelnum from named parameter or first positional key
    if not request.args:
        raise APIError("Missing required query parameter: channelnum", "MISSING_PARAMETER")

    channelnum_raw = request.args.get("channelnum")
    if channelnum_raw is None:
        channelnum_raw = list(request.args.keys())[0]

    channel_com = convert_channel_to_com_index(channelnum_raw)

    result = vv_instance.ChannelUnit(channel_com)

    return jsonify(
        success_response({"result": result, "channelnum": int(channelnum_raw), "internal_channelnum": channel_com})
    )


@data_retrieval_bp.route("/channellabel", methods=["GET"])
@handle_errors
@with_vibrationview
def channel_label(vv_instance: Any) -> Response:
    """
    Get the channel unit label associated with channel number (1-based)

    COM Method: ChannelLabel(channelnum - 1)
    Channel numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.

    Query Parameters:
        channelnum (no parameter name required)

    Example:
        GET /api/v1/channellabel?1
    """
    # Get channelnum from named parameter or first positional key
    if not request.args:
        raise APIError("Missing required query parameter: channelnum", "MISSING_PARAMETER")

    channelnum_raw = request.args.get("channelnum")
    if channelnum_raw is None:
        channelnum_raw = list(request.args.keys())[0]

    channel_com = convert_channel_to_com_index(channelnum_raw)

    result = vv_instance.ChannelLabel(channel_com)

    return jsonify(
        success_response({"result": result, "channelnum": int(channelnum_raw), "internal_channelnum": channel_com})
    )


# ============================================================================
# CONTROL METADATA (1-based indexing with conversion)
# ============================================================================


@data_retrieval_bp.route("/controlunit", methods=["GET"])
@handle_errors
@with_vibrationview
def control_unit(vv_instance: Any) -> Response:
    """
    Get control loop units

    COM Method: ControlUnit(loopnum - 1)
    Loop numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.

    Query Parameters:
        loopnum: integer - Loop number (1-based, defaults to 1 if no parameters)

    Examples:
        GET /api/v1/controlunit (defaults to loop 1)
        GET /api/v1/controlunit?loopnum=2
        GET /api/v1/controlunit?2
    """
    # Determine loop number - default to 1 if no parameters
    loopnum: int = 1
    if request.args:
        try:
            # Try to get 'loopnum' parameter first, then fall back to first key
            loopnum_param = request.args.get("loopnum", type=int)
            if loopnum_param is not None:
                loopnum = loopnum_param
            else:
                # If no 'loopnum' parameter, try the first key as the value
                first_key = list(request.args.keys())[0]
                loopnum = int(first_key)
        except (ValueError, IndexError):
            raise APIError("loopnum must be an integer", "INVALID_PARAMETER")

    # Convert from 1-based to 0-based
    if loopnum < 1:
        raise APIError(f"loopnum must be >= 1 (1-based indexing), got {loopnum}", "INVALID_PARAMETER")

    loop_num_0based = loopnum - 1

    result = vv_instance.ControlUnit(loop_num_0based)
    return jsonify(
        success_response(
            {
                "result": result,
                "loopnum": loopnum,
            },
            f"ControlUnit retrieved for loop {loopnum}: {result}",
        )
    )


@data_retrieval_bp.route("/controllabel", methods=["GET"])
@handle_errors
@with_vibrationview
def control_label(vv_instance: Any) -> Response:
    """
    Get control loop label

    COM Method: ControlLabel(loopnum - 1)
    Loop numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.

    Query Parameters:
        loopnum: integer - Loop number (1-based, defaults to 1 if no parameters)

    Examples:
        GET /api/v1/controllabel (defaults to loop 1)
        GET /api/v1/controllabel?loopnum=2
        GET /api/v1/controllabel?2
    """
    # Determine loop number - default to 1 if no parameters
    loopnum: int = 1
    if request.args:
        try:
            # Try to get 'loopnum' parameter first, then fall back to first key
            loopnum_param = request.args.get("loopnum", type=int)
            if loopnum_param is not None:
                loopnum = loopnum_param
            else:
                # If no 'loopnum' parameter, try the first key as the value
                first_key = list(request.args.keys())[0]
                loopnum = int(first_key)
        except (ValueError, IndexError):
            raise APIError("loopnum must be an integer", "INVALID_PARAMETER")

    # Convert from 1-based to 0-based
    if loopnum < 1:
        raise APIError(f"loopnum must be >= 1 (1-based indexing), got {loopnum}", "INVALID_PARAMETER")

    loop_num_0based = loopnum - 1

    result = vv_instance.ControlLabel(loop_num_0based)
    return jsonify(
        success_response(
            {"result": result, "loopnum": loopnum, "internal_loopnum": loop_num_0based},
            f"ControlLabel retrieved for loop {loopnum}: {result}",
        )
    )


# ============================================================================
# RAW DATA FILE RETRIEVAL
# ============================================================================


@data_retrieval_bp.route("/getdatafile", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def get_data_file(vv_instance: Any) -> Response:
    """
    Get Raw VibrationVIEW Data File

    Retrieves the most recent VibrationVIEW data file (.vrd) and returns it as raw binary data.
    Uses the same parameter scheme as generatetxt for consistency.

    Request Body (JSON, optional) or Query Parameters:
        file_path: string - Path to specific VibrationVIEW data file (optional - uses last data file if not specified)

    Note: Returns the raw .vrd file as binary data, not JSON.
          Use Content-Type: application/octet-stream for binary download.

    Example: GET /api/v1/getdatafile (uses last data file)
             GET /api/v1/getdatafile?file_path=specific_file.vrd
             POST /api/v1/getdatafile with JSON body: {"file_path": "specific_file.vrd"}
    """
    # Get parameters from JSON body (optional) or query parameters
    try:
        request_data = request.get_json() or {}
    except Exception:
        # If JSON parsing fails, use empty dict and fall back to query parameters
        request_data = {}

    file_path = request_data.get("file_path") or request.args.get("file_path")

    # If file_path is not provided, use the last data file from VibrationVIEW
    if not file_path:
        file_path = get_last_data_file(vv_instance)

    # Validate file_path security and existence
    try:
        validated_file_path = validate_file_path(file_path, "data file retrieval")
    except PathValidationError as e:
        raise APIError(str(e), "PATH_VALIDATION_ERROR", 403)

    if not os.path.exists(validated_file_path):
        raise APIError(f"File not found: {validated_file_path}", "FILE_NOT_FOUND", 404)

    # Use validated path
    file_path = validated_file_path

    # Get file info
    file_name = os.path.basename(file_path)

    # Return raw file as binary download
    return send_file(file_path, as_attachment=True, download_name=file_name, mimetype="application/octet-stream")
