# ============================================================================
# FILE: routes/virtual_channels.py (Virtual Channels Routes)
# ============================================================================

"""
Virtual Channels Routes - 1:1 VibrationVIEW COM Interface Mapping
Virtual channel management operations matching exact COM method signatures
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from utils.decorators import handle_errors
from utils.response_helpers import error_response, success_response
from utils.utils import get_filename_from_request, process_file_upload
from utils.vv_manager import with_vibrationview

# Create blueprint
virtual_channels_bp = Blueprint("virtual_channels", __name__)

logger = logging.getLogger(__name__)


@virtual_channels_bp.route("/docs/virtual_channels", methods=["GET"])
def get_documentation() -> Response:
    """Get virtual channels module documentation"""
    docs = {
        "module": "virtual_channels",
        "description": "1:1 mapping of VibrationVIEW COM virtual channel methods",
        "com_object": "VibrationVIEW.Application",
        "endpoints": {
            "POST /removeallvirtualchannels": {
                "description": "Remove all virtual channels from the current test",
                "com_method": "RemoveAllVirtualChannels()",
                "parameters": "None",
                "returns": "bool - Success status",
                "example": "POST /api/v1/removeallvirtualchannels",
            },
            "POST|PUT /importvirtualchannels": {
                "description": "Upload and import a virtual channels file, OR import existing file by path",
                "com_method": "ImportVirtualChannels(filepath)",
                "modes": {
                    "With file content (upload mode)": {
                        "Option 1 (multipart/form-data)": "any file field (filename auto-detected)",
                        "Option 2 (raw binary)": "filename query parameter required, binary body",
                    },
                    "Without file content": "filename query parameter required",
                },
                "returns": "object - Status, file path",
                "examples": [
                    "POST /api/v1/importvirtualchannels with multipart/form-data (upload + import)",
                    "POST /api/v1/importvirtualchannels?filename=channels.vvc with raw binary body (upload + import)",
                    "POST /api/v1/importvirtualchannels?filename=channels.vvc (import existing file)",
                ],
            },
        },
        "notes": [
            "All endpoints are 1:1 COM method mappings",
            "RemoveAllVirtualChannels clears all virtual channels from the current test",
            "ImportVirtualChannels loads virtual channel definitions from a file",
            "PUT method allows uploading and importing in one operation",
        ],
    }
    return jsonify(docs)


@virtual_channels_bp.route("/removeallvirtualchannels", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def remove_all_virtual_channels(vv_instance: Any) -> Response:
    """
    Remove All Virtual Channels

    COM Method: RemoveAllVirtualChannels()
    Removes all virtual channels from the current test configuration.

    Example: POST /api/v1/removeallvirtualchannels
    """
    result = vv_instance.RemoveAllVirtualChannels()

    return jsonify(success_response({"result": result}, "RemoveAllVirtualChannels command executed"))


@virtual_channels_bp.route("/importvirtualchannels", methods=["GET", "POST", "PUT"])
@handle_errors
@with_vibrationview
def import_virtual_channels(vv_instance: Any) -> Response | tuple[Response, int]:
    """
    Import Virtual Channels from File

    COM Method: ImportVirtualChannels(filepath)
    Imports virtual channel definitions from a configuration file.

    GET: Import existing file by path
        Query Parameters:
            filename: string - Virtual channels configuration filename (named parameter)
            OR unnamed parameter: string - Filename as first URL parameter
        Example: GET /api/v1/importvirtualchannels?filename=channels.vvc

    POST/PUT: Upload file and import, OR import existing file by path
        If request includes file content:
            Option 1 - multipart/form-data (recommended):
                Form Field: any - The config file (original filename auto-detected)
                Example: POST /api/v1/importvirtualchannels with Content-Type: multipart/form-data

            Option 2 - Raw binary body:
                Query Parameters: filename (required for raw binary)
                Body: Binary file content
                Example: PUT /api/v1/importvirtualchannels?filename=channels.vvc (with binary body)

        If no file content:
            Query Parameters:
                filename: string - Virtual channels configuration filename (named parameter)
                OR unnamed parameter: string - Filename as first URL parameter
            Example: POST /api/v1/importvirtualchannels?filename=channels.vvc
    """
    # Check for file upload (PUT/POST only)
    if request.method in ("PUT", "POST"):
        file_path, filename, upload_error = process_file_upload()
        if upload_error:
            return jsonify(upload_error[0]), upload_error[1]

        if file_path:

            # Import the uploaded virtual channels file
            vv_instance.ImportVirtualChannels(file_path)

            return jsonify(
                success_response(
                    {"result": True, "filepath": filename, "file_uploaded": True},
                    f"Upload and ImportVirtualChannels command executed: {filename}",
                )
            )

    # No file upload - import existing file by path
    filename = get_filename_from_request()

    if not filename:
        return jsonify(error_response("Missing required query parameter: filename", "MISSING_PARAMETER")), 400

    vv_instance.ImportVirtualChannels(filename)

    return jsonify(
        success_response({"result": True, "filepath": filename}, f"ImportVirtualChannels command executed: {filename}")
    )
