# ============================================================================
# GUI Control Routes
# ============================================================================

"""
GUI Control Routes - 1:1 VibrationVIEW COM Interface Mapping
GUI and window management operations matching exact COM method signatures
"""

import logging
from typing import Any

from flask import Blueprint, Response, jsonify, request

from utils.decorators import handle_errors
from utils.exceptions import APIError
from utils.response_helpers import success_response
from utils.utils import get_filename_from_request, process_file_upload
from utils.vv_manager import with_vibrationview

# Create blueprint
gui_control_bp = Blueprint("gui_control", __name__)

logger = logging.getLogger(__name__)


@gui_control_bp.route("/docs/gui_control", methods=["GET"])
def get_documentation() -> Response:
    """Get GUI control module documentation"""
    docs = {
        "module": "gui_control",
        "description": "1:1 mapping of VibrationVIEW COM GUI control methods",
        "com_object": "VibrationVIEW.Application",
        "endpoints": {
            "Test Editing": {
                "POST|PUT /edittest": {
                    "description": "Upload and edit test file, OR edit existing by path",
                    "com_method": "EditTest(szTestName)",
                    "modes": {
                        "With file content (upload)": "multipart/form-data or raw binary + filename param",
                        "Without file content": "filename query parameter to edit existing",
                    },
                    "returns": "Success status with file path",
                    "examples": [
                        "POST /api/v1/edittest with multipart/form-data (upload + edit)",
                        "PUT /api/v1/edittest?filename=test.vsp with binary body",
                        "POST /api/v1/edittest?filename=test.vsp (edit existing)",
                    ],
                },
                "POST /abortedit": {
                    "description": "Abort any open Edit session",
                    "com_method": "AbortEdit()",
                    "parameters": "None",
                    "returns": "HRESULT - Success status from COM method",
                },
            },
            "Window Management": {
                "POST /minimize": {
                    "description": "Minimize VibrationVIEW",
                    "com_method": "Minimize()",
                    "parameters": "None",
                    "returns": "HRESULT - Success status from COM method",
                },
                "POST /restore": {
                    "description": "Restore VibrationVIEW",
                    "com_method": "Restore()",
                    "parameters": "None",
                    "returns": "HRESULT - Success status from COM method",
                },
                "POST /maximize": {
                    "description": "Maximize VibrationVIEW",
                    "com_method": "Maximize()",
                    "parameters": "None",
                    "returns": "HRESULT - Success status from COM method",
                },
                "POST /activate": {
                    "description": "Activate VibrationVIEW",
                    "com_method": "Activate()",
                    "parameters": "None",
                    "returns": "HRESULT - Success status from COM method",
                },
            },
        },
        "notes": [
            "POST/PUT requests with parameters use URL query strings",
            "All methods return HRESULT status codes",
            "EditTest requires valid test file name",
            "Window management methods affect VibrationVIEW main window",
            "COM interface uses 0-based indexing for all arrays",
        ],
    }
    return jsonify(docs)


# Test Editing Control
@gui_control_bp.route("/edittest", methods=["GET", "POST", "PUT"])
@handle_errors
@with_vibrationview
def edit_test(vv_instance: Any) -> Response:
    """
    Edit VibrationVIEW Test

    COM Method: EditTest(szTestName)
    Opens the specified test for editing in VibrationVIEW.

    GET: Edit existing file by path
        Query Parameters:
            filename: string - Test filename (named parameter)
            OR unnamed parameter: string - Test filename as first URL parameter
        Example: GET /api/v1/edittest?filename=test1.vsp

    POST/PUT: Upload file and edit, OR edit existing file by path
        If request includes file content:
            Option 1 - multipart/form-data (recommended):
                Form Field: any - The test file (original filename auto-detected)
                Example: POST /api/v1/edittest with Content-Type: multipart/form-data

            Option 2 - Raw binary body:
                Query Parameters: filename (required for raw binary)
                Body: Binary file content
                Example: POST /api/v1/edittest?filename=test1.vsp (with binary body)

        If no file content:
            Query Parameters:
                filename: string - Test filename (named parameter)
                OR unnamed parameter: string - Test filename as first URL parameter
            Example: POST /api/v1/edittest?filename=test1.vsp
    """
    # Check for file upload (PUT/POST only)
    if request.method in ("PUT", "POST"):
        file_path, filename = process_file_upload()
        if file_path:
            vv_instance.EditTest(file_path)

            return jsonify(
                success_response(
                    {"result": True, "filepath": filename, "file_uploaded": True},
                    f"Upload and EditTest command executed: {filename}",
                )
            )

    # No file upload - edit existing file by path
    filename = get_filename_from_request()

    if not filename:
        raise APIError("Missing required query parameter: filename", "MISSING_PARAMETER")

    result = vv_instance.EditTest(filename)

    return jsonify(success_response({"result": result, "filepath": filename}, f"EditTest command executed: {filename}"))


@gui_control_bp.route("/abortedit", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def abort_edit(vv_instance: Any) -> Response:
    """
    Abort Edit Session

    COM Method: AbortEdit()
    Aborts any currently open edit session without saving changes.
    """
    vv_instance.AbortEdit()
    result = True  # If no exception, assume success

    return jsonify(success_response({"result": result}, "AbortEdit command executed"))


# Window Management Control
@gui_control_bp.route("/minimize", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def minimize(vv_instance: Any) -> Response:
    """
    Minimize VibrationVIEW

    COM Method: Minimize()
    Minimizes the VibrationVIEW application window.
    """
    vv_instance.Minimize()
    result = True  # If no exception, assume success

    return jsonify(success_response({"result": result}, "Minimize command executed"))


@gui_control_bp.route("/restore", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def restore(vv_instance: Any) -> Response:
    """
    Restore VibrationVIEW

    COM Method: Restore()
    Restores the VibrationVIEW application window from minimized state.
    """
    vv_instance.Restore()
    result = True  # If no exception, assume success

    return jsonify(success_response({"result": result}, "Restore command executed"))


@gui_control_bp.route("/maximize", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def maximize(vv_instance: Any) -> Response:
    """
    Maximize VibrationVIEW

    COM Method: Maximize()
    Maximizes the VibrationVIEW application window.
    """
    vv_instance.Maximize()
    result = True  # If no exception, assume success

    return jsonify(success_response({"result": result}, "Maximize command executed"))


@gui_control_bp.route("/activate", methods=["GET", "POST"])
@handle_errors
@with_vibrationview
def activate(vv_instance: Any) -> Response:
    """
    Activate VibrationVIEW

    COM Method: Activate()
    Brings the VibrationVIEW application window to the foreground and activates it.
    """
    vv_instance.Activate()
    result = True  # If no exception, assume success

    return jsonify(success_response({"result": result}, "Activate command executed"))
