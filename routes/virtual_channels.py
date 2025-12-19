# ============================================================================
# FILE: routes/virtual_channels.py (Virtual Channels Routes)
# ============================================================================

"""
Virtual Channels Routes - 1:1 VibrationVIEW COM Interface Mapping
Virtual channel management operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from urllib.parse import unquote
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import handle_binary_upload, detect_file_upload, get_filename_from_request
import logging
import config
import os

# Create blueprint
virtual_channels_bp = Blueprint('virtual_channels', __name__)

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit


@virtual_channels_bp.route('/docs/virtual_channels', methods=['GET'])
def get_documentation():
    """Get virtual channels module documentation"""
    docs = {
        'module': 'virtual_channels',
        'description': '1:1 mapping of VibrationVIEW COM virtual channel methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'POST /removeallvirtualchannels': {
                'description': 'Remove all virtual channels from the current test',
                'com_method': 'RemoveAllVirtualChannels()',
                'parameters': 'None',
                'returns': 'bool - Success status',
                'example': 'POST /api/v1/removeallvirtualchannels'
            },
            'GET|POST /importvirtualchannels': {
                'description': 'Import virtual channels from a configuration file',
                'com_method': 'ImportVirtualChannels(filepath)',
                'parameters': {
                    'filename': 'string - Virtual channels configuration filename (named parameter)',
                    'OR unnamed parameter': 'string - Filename as first URL parameter'
                },
                'returns': 'bool - Success status',
                'examples': [
                    'POST /api/v1/importvirtualchannels?filename=channels.vvc',
                    'POST /api/v1/importvirtualchannels?channels.vvc'
                ]
            },
            'PUT /importvirtualchannels': {
                'description': 'Upload and import virtual channels configuration file',
                'com_method': 'ImportVirtualChannels(filepath)',
                'parameters': {
                    'filename': 'string - Configuration filename (URL parameter)',
                    'OR unnamed parameter': 'string - Filename as first URL parameter'
                },
                'headers': {
                    'Content-Length': 'Required - File size in bytes (max 10MB)'
                },
                'body': 'Binary file content',
                'returns': 'dict - Success status and file info',
                'example': 'PUT /api/v1/importvirtualchannels?filename=channels.vvc (with binary file in body)'
            }
        },
        'notes': [
            'All endpoints are 1:1 COM method mappings',
            'RemoveAllVirtualChannels clears all virtual channels from the current test',
            'ImportVirtualChannels loads virtual channel definitions from a file',
            'PUT method allows uploading and importing in one operation'
        ]
    }
    return jsonify(docs)


@virtual_channels_bp.route('/removeallvirtualchannels', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def remove_all_virtual_channels(vv_instance):
    """
    Remove All Virtual Channels

    COM Method: RemoveAllVirtualChannels()
    Removes all virtual channels from the current test configuration.

    Example: POST /api/v1/removeallvirtualchannels
    """
    result = vv_instance.RemoveAllVirtualChannels()

    return jsonify(success_response(
        {'result': result},
        "RemoveAllVirtualChannels command executed"
    ))


@virtual_channels_bp.route('/importvirtualchannels', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def import_virtual_channels(vv_instance):
    """
    Import Virtual Channels from File

    COM Method: ImportVirtualChannels(filepath)
    Imports virtual channel definitions from a configuration file.

    Query Parameters:
        filename: string - Virtual channels configuration filename (named parameter)
        OR unnamed parameter: string - Filename as first URL parameter

    Examples:
        POST /api/v1/importvirtualchannels?filename=channels.vvc
        POST /api/v1/importvirtualchannels?channels.vvc
    """
    # Get filename from parameters - check named parameter first, then unnamed
    filename = request.args.get("filename")

    # If no 'filename' parameter, try to get the first unnamed parameter
    if filename is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters
            filename = unquote(query_string)

    if not filename:
        return jsonify(error_response(
            'Missing required query parameter: filename (or unnamed filename parameter)',
            'MISSING_PARAMETER'
        )), 400

    # Use filename as provided (can be full path or just filename)
    filepath = filename

    result = vv_instance.ImportVirtualChannels(filepath)

    return jsonify(success_response(
        {
            'result': result,
            'filepath': filepath
        },
        f"ImportVirtualChannels command executed: {filename}"
    ))


@virtual_channels_bp.route('/importvirtualchannels', methods=['POST', 'PUT'])
@handle_errors
@with_vibrationview
def upload_and_import_virtual_channels(vv_instance):
    """
    Upload and Import Virtual Channels Configuration File

    COM Method: ImportVirtualChannels(filepath)
    Uploads a virtual channels configuration file and imports it.

    POST/PUT: Upload file
        If request includes file content:
            Option 1 - multipart/form-data (recommended):
                Form Field: any - The config file (original filename auto-detected)
                Example: POST /api/v1/importvirtualchannels with Content-Type: multipart/form-data

            Option 2 - Raw binary body:
                Query Parameters: filename (required for raw binary)
                Body: Binary file content
                Example: PUT /api/v1/importvirtualchannels?filename=channels.vvc (with binary body)
    """
    # Detect file upload (multipart or raw binary)
    upload_result = detect_file_upload()
    filename, binary_data, content_length = upload_result

    # Check if detect_file_upload returned an error
    if isinstance(filename, dict):
        return jsonify(filename), binary_data  # filename is error dict, binary_data is status code

    if filename is None:
        return jsonify(error_response(
            'Missing file: provide via multipart/form-data or raw binary with filename parameter',
            'MISSING_FILE'
        )), 400

    # Handle file upload
    result, error, status_code = handle_binary_upload(filename, binary_data)

    if error:
        return jsonify(error), status_code

    file_path = result['FilePath']

    # Import the uploaded virtual channels file
    try:
        import_result = vv_instance.ImportVirtualChannels(file_path)
    except Exception as e:
        return jsonify(error_response(
            f'File uploaded but failed to import virtual channels "{filename}": {str(e)}',
            'IMPORT_ERROR'
        )), 500

    return jsonify(success_response(
        {
            'result': import_result,
            'filepath': filename,
            'file_uploaded': True
        },
        f"Virtual channels file '{filename}' uploaded and imported successfully"
    ))
