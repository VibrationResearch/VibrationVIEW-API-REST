# ============================================================================
# GUI Control Routes 
# ============================================================================

"""
GUI Control Routes - 1:1 VibrationVIEW COM Interface Mapping
GUI and window management operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import handle_binary_upload, detect_file_upload, get_filename_from_request
import logging
import os
import config

# Create blueprint
gui_control_bp = Blueprint('gui_control', __name__)

logger = logging.getLogger(__name__)

@gui_control_bp.route('/docs/gui_control', methods=['GET'])
def get_documentation():
    """Get GUI control module documentation"""
    docs = {
        'module': 'gui_control',
        'description': '1:1 mapping of VibrationVIEW COM GUI control methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Test Editing': {
                'GET /edittest': {
                    'description': 'Edit existing test by path',
                    'com_method': 'EditTest(szTestName)',
                    'parameters': {
                        'filename': 'string - Test filename as query parameter'
                    },
                    'returns': 'Success status',
                    'example': 'GET /api/v1/edittest?filename=test1.vsp'
                },
                'POST|PUT /edittest': {
                    'description': 'Upload and edit test file, OR edit existing by path',
                    'com_method': 'EditTest(szTestName)',
                    'modes': {
                        'With file content (upload)': 'multipart/form-data or raw binary + filename param',
                        'Without file content': 'filename query parameter to edit existing'
                    },
                    'returns': 'Success status with file path',
                    'examples': [
                        'POST /api/v1/edittest with multipart/form-data (upload + edit)',
                        'PUT /api/v1/edittest?filename=test.vsp with binary body',
                        'POST /api/v1/edittest?filename=test.vsp (edit existing)'
                    ]
                },
                'GET /abortedit': {
                    'description': 'Abort any open Edit session',
                    'com_method': 'AbortEdit()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                }
            },
            'Window Management': {
                'GET /minimize': {
                    'description': 'Minimize VibrationVIEW',
                    'com_method': 'Minimize()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /restore': {
                    'description': 'Restore VibrationVIEW',
                    'com_method': 'Restore()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /maximize': {
                    'description': 'Maximize VibrationVIEW',
                    'com_method': 'Maximize()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /activate': {
                    'description': 'Activate VibrationVIEW',
                    'com_method': 'Activate()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                }
            }
        },
        'notes': [
            'GET requests with parameters use URL query strings',
            'All methods return HRESULT status codes',
            'EditTest requires valid test file name',
            'Window management methods affect VibrationVIEW main window',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

# Test Editing Control
@gui_control_bp.route('/edittest', methods=['GET', 'POST', 'PUT'])
@handle_errors
@with_vibrationview
def edit_test(vv_instance):
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
    if request.method in ('PUT', 'POST'):
        upload_result = detect_file_upload()
        filename, binary_data, content_length = upload_result

        # Check if detect_file_upload returned an error
        if isinstance(filename, dict):
            return jsonify(filename), binary_data  # filename is error dict, binary_data is status code

        if filename is not None:
            # File upload detected - save and edit
            result, error, status_code = handle_binary_upload(filename, binary_data)
            if error:
                return jsonify(error), status_code

            file_path = result['FilePath']
            try:
                vv_instance.EditTest(file_path)
            except Exception as e:
                return jsonify(error_response(
                    f'File uploaded but failed to edit test "{filename}": {str(e)}',
                    'EDIT_TEST_ERROR',
                    f"EditTest command failed: {filename}"
                )), 500

            return jsonify(success_response(
                {
                    'result': True,
                    'filepath': filename,
                    'file_uploaded': True
                },
                f"Upload and EditTest command executed: {filename}"
            ))

    # No file upload - edit existing file by path
    filename = get_filename_from_request()

    if not filename:
        return jsonify(error_response(
            'Missing required query parameter: filename',
            'MISSING_PARAMETER'
        )), 400

    try:
        result = vv_instance.EditTest(filename)
    except Exception as e:
        return jsonify(error_response(
            f'Failed to edit test "{filename}": {str(e)}',
            'EDIT_TEST_ERROR',
            f"EditTest command failed: {filename}"
        )), 500

    return jsonify(success_response(
        {
            'result': result,
            'filepath': filename
        },
        f"EditTest command executed: {filename}"
    ))

@gui_control_bp.route('/abortedit', methods=['GET'])
@handle_errors
@with_vibrationview
def abort_edit(vv_instance):
    """
    Abort Edit Session
    
    COM Method: AbortEdit()
    Aborts any currently open edit session without saving changes.
    """
    result = vv_instance.AbortEdit()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"AbortEdit command executed - Result: {result}"
    ))

# Window Management Control
@gui_control_bp.route('/minimize', methods=['GET'])
@handle_errors
@with_vibrationview
def minimize(vv_instance):
    """
    Minimize VibrationVIEW
    
    COM Method: Minimize()
    Minimizes the VibrationVIEW application window.
    """
    result = vv_instance.Minimize()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Minimize command executed - Result: {result}"
    ))

@gui_control_bp.route('/restore', methods=['GET'])
@handle_errors
@with_vibrationview
def restore(vv_instance):
    """
    Restore VibrationVIEW
    
    COM Method: Restore()
    Restores the VibrationVIEW application window from minimized state.
    """
    result = vv_instance.Restore()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Restore command executed - Result: {result}"
    ))

@gui_control_bp.route('/maximize', methods=['GET'])
@handle_errors
@with_vibrationview
def maximize(vv_instance):
    """
    Maximize VibrationVIEW
    
    COM Method: Maximize()
    Maximizes the VibrationVIEW application window.
    """
    result = vv_instance.Maximize()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Maximize command executed - Result: {result}"
    ))

@gui_control_bp.route('/activate', methods=['GET'])
@handle_errors
@with_vibrationview
def activate(vv_instance):
    """
    Activate VibrationVIEW
    
    COM Method: Activate()
    Brings the VibrationVIEW application window to the foreground and activates it.
    """
    result = vv_instance.Activate()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Activate command executed - Result: {result}"
    ))