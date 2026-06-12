# ============================================================================
# FILE: routes/virtual_channels.py (Virtual Channels Routes)
# ============================================================================

"""
Virtual Channels Routes - 1:1 VibrationVIEW COM Interface Mapping
Virtual channel management operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import handle_binary_upload, detect_file_upload, get_filename_from_request
import logging

# Create blueprint
virtual_channels_bp = Blueprint('virtual_channels', __name__)

logger = logging.getLogger(__name__)



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
            'POST|PUT /importvirtualchannels': {
                'description': 'Import virtual channels from a configuration file, or upload and import',
                'com_method': 'ImportVirtualChannels(filepath)',
                'parameters': {
                    'filename': 'string - Virtual channels configuration filename (named parameter)',
                    'OR unnamed parameter': 'string - Filename as first URL parameter'
                },
                'body': 'Optional binary file content (multipart/form-data or raw binary)',
                'returns': 'bool - Success status',
                'examples': [
                    'POST /api/v1/importvirtualchannels?filename=channels.vvc',
                    'PUT /api/v1/importvirtualchannels?filename=channels.vvc (with binary body)'
                ]
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


@virtual_channels_bp.route('/importvirtualchannels', methods=['POST', 'PUT'])
@handle_errors
@with_vibrationview
def import_virtual_channels(vv_instance):
    """
    Import Virtual Channels from File

    COM Method: ImportVirtualChannels(filepath)
    Imports virtual channel definitions from a configuration file.

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
    # Check for file upload
    upload_result = detect_file_upload()
    filename, binary_data, content_length = upload_result

    # Check if detect_file_upload returned an error
    if isinstance(filename, dict):
        return jsonify(filename), binary_data  # filename is error dict, binary_data is status code

    if filename is not None:
        # File upload detected - save and import
        result, error, status_code = handle_binary_upload(filename, binary_data)

        if error:
            return jsonify(error), status_code

        file_path = result['FilePath']

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

    # No file upload - import by filename from query parameter
    filename = get_filename_from_request()

    if not filename:
        return jsonify(error_response(
            'Missing required query parameter: filename (or unnamed filename parameter)',
            'MISSING_PARAMETER'
        )), 400

    result = vv_instance.ImportVirtualChannels(filename)

    return jsonify(success_response(
        {
            'result': result,
            'filepath': filename
        },
        f"ImportVirtualChannels command executed: {filename}"
    ))
