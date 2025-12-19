# ============================================================================
# FILE: routes/report_generation.py (Report Generation Routes) - v1
# ============================================================================

"""
Report Generation Routes - VibrationVIEW Command Line Operations
File generation operations using VibrationVIEW command line interface
"""

from flask import Blueprint, request, jsonify, send_file
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import handle_binary_upload, detect_file_upload
from utils.vv_manager import with_vibrationview
from utils.path_validator import validate_file_path, validate_output_path, PathValidationError
from vibrationviewapi import GenerateReportFromVV, GenerateTXTFromVV, GenerateUFFFromVV
import logging
import os
import tempfile
import zipfile
import io
from datetime import datetime

# Create blueprint
report_generation_bp = Blueprint('report_generation', __name__)

logger = logging.getLogger(__name__)

@report_generation_bp.route('/docs/report_generation', methods=['GET'])
def get_documentation():
    """Get report generation module documentation"""
    docs = {
        'module': 'report_generation',
        'description': 'VibrationVIEW command line file generation operations',
        'endpoints': {
            'POST /generatereport': {
                'description': 'Generate a report file from VibrationVIEW data using a template (supports file upload or file path)',
                'function': 'GenerateReportFromVV(filePath, templateName, outputName)',
                'modes': {
                    'upload': 'Upload .vrd file in body with query parameters',
                    'filepath': 'Specify existing file path via JSON body or query parameters'
                },
                'upload_parameters': {
                    'template_name': 'string - Query parameter with report template name (required for upload)',
                    'output_name': 'string - Query parameter with desired output filename (required for upload)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)',
                    'headers': 'Content-Length required, Content-Type: application/octet-stream recommended'
                },
                'filepath_parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'template_name': 'string - Name of the report template to use (optional - uses "Test Report.rtf" if not specified)',
                    'output_name': 'string - Desired name of the generated report file (optional - auto-generated with same extension as template_name if not specified)'
                },
                'returns': 'object - Success status, path to generated report file, and file content (text or base64-encoded binary)',
                'note': 'Returns file content directly in response. Text files (HTML, TXT, CSV) returned as text, binary files (PDF, DOC) returned as base64',
                'examples': {
                    'upload': 'POST /api/v1/generatereport?template_name=Standard%20Report&output_name=report.pdf (with .vrd file in body)',
                    'filepath': 'POST /api/v1/generatereport with JSON body: {"file_path": "test.vrd", "template_name": "Standard Report", "output_name": "report.pdf"} or query params'
                }
            },
            'POST /generatetxt': {
                'description': 'Generate text files from VibrationVIEW data (supports file upload or file path) - creates one file per plot in the datafile',
                'function': 'GenerateTXTFromVV(filePath, outputName)',
                'modes': {
                    'upload': 'Upload .vrd file in body with query parameters',
                    'filepath': 'Specify existing file path via JSON body or query parameters'
                },
                'upload_parameters': {
                    'output_name': 'string - Query parameter with desired output filename (required for upload)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)',
                    'headers': 'Content-Length required, Content-Type: application/octet-stream recommended'
                },
                'filepath_parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'output_name': 'string - Base name for generated text files (optional - auto-generated if not specified)'
                },
                'returns': 'object - Success status, paths to all generated text files (basename-1.txt, basename-2.txt, etc.), and combined file contents',
                'note': 'Creates multiple files with pattern basename-N.txt where N corresponds to each plot in the VibrationVIEW data file',
                'examples': {
                    'upload': 'POST /api/v1/generatetxt?output_name=data.txt (with .vrd file in body)',
                    'filepath': 'POST /api/v1/generatetxt with JSON body: {"file_path": "test.vrd", "output_name": "data.txt"} or query params'
                }
            },
            'POST /generateuff': {
                'description': 'Generate UFF (Universal File Format) files from VibrationVIEW data (supports file upload or file path) - creates one file per plot in the datafile',
                'function': 'GenerateUFFFromVV(filePath, outputName)',
                'modes': {
                    'upload': 'Upload .vrd file in body with query parameters',
                    'filepath': 'Specify existing file path via JSON body or query parameters'
                },
                'upload_parameters': {
                    'output_name': 'string - Query parameter with desired output filename (required for upload)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)',
                    'headers': 'Content-Length required, Content-Type: application/octet-stream recommended'
                },
                'filepath_parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'output_name': 'string - Base name for generated UFF files (optional - auto-generated with .uff extension if not specified)'
                },
                'returns': 'object - Success status, paths to all generated UFF files (basename-1.uff, basename-2.uff, etc.), and combined file contents',
                'note': 'Creates multiple files with pattern basename-N.uff where N corresponds to each plot in the VibrationVIEW data file',
                'examples': {
                    'upload': 'POST /api/v1/generateuff?output_name=data.uff (with .vrd file in body)',
                    'filepath': 'POST /api/v1/generateuff with JSON body: {"file_path": "test.vrd", "output_name": "data.uff"} or query params'
                }
            },
            'GET /datafile': {
                'description': 'Get the raw VibrationVIEW data file (.vrd) content without any processing',
                'parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)'
                },
                'returns': 'binary - Raw .vrd file content as binary data',
                'note': 'Returns the unprocessed data file directly as binary. Useful for downloading or transferring raw test data.',
                'example': 'GET /api/v1/datafile or GET /api/v1/datafile?file_path=test.vrd'
            },
            'GET /datafiles': {
                'description': 'Get all data files generated during the completed test as a zip archive',
                'parameters': {},
                'returns': 'binary - Zip file containing all data files from the completed test',
                'note': 'Returns a zip archive of all .vrd data files generated during the completed test. Useful for bulk download of test data.',
                'example': 'GET /api/v1/datafiles'
            },
            'PUT /generatetxt': {
                'description': 'Upload VibrationVIEW data file and generate a text file',
                'function': 'GenerateTXTFromVV(filePath, outputName)',
                'parameters': {
                    'output_name': 'string - Query parameter with desired output filename (required)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)'
                },
                'headers': {
                    'Content-Length': 'required - File size in bytes'
                },
                'returns': 'object - Success status, path to generated text file, and file content',
                'example': 'PUT /api/v1/generatetxt?output_name=data.txt (with .vrd file in body)'
            },
        },
        'notes': [
            'All operations use VibrationVIEW command line interface',
            'Files are generated in the configured report folder or specified output path',
            'Operations may take time depending on file size and complexity',
            'Generated files are saved to disk and path is returned',
            'Report generation requires a valid template name',
            'TXT and UFF generation work with VibrationVIEW data files (.vrd)',
            'TXT and UFF generation creates one file per plot in the VibrationVIEW data file',
            'Multiple files are generated with naming pattern: basename-1.txt, basename-2.txt, etc.',
            'If output_name contains a path, that path will be used; otherwise files go to temporary folder',
            'POST endpoints work with existing files by file path or use last data file if not specified',
            'If file_path is not provided in POST requests, uses VibrationVIEW.GetReportField("LastDataFile")'
        ]
    }
    return jsonify(docs)


@report_generation_bp.route('/generatereport', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def generate_report(vv_instance):
    """
    Generate Report File from VibrationVIEW Data

    Function: GenerateReportFromVV(filePath, templateName, outputName)
    Generates a report file using VibrationVIEW command line interface
    with the specified template.

    Two modes of operation:
    1. File Upload Mode: POST with binary .vrd file in body and query parameters
    2. File Path Mode: POST with JSON body or query parameters specifying existing file path

    File Upload Mode:
        Query Parameters:
            template_name: string - Name of the report template to use (required for upload mode)
            output_name: string - Desired name of the generated report file (required for upload mode)
        Headers:
            Content-Length: Required for upload mode - File size in bytes (max 100MB)
            Content-Type: application/octet-stream (for binary upload)
        Body: Binary VibrationVIEW data file content (.vrd)

    File Path Mode:
        Request Body (JSON, optional) or Query Parameters:
            file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
            template_name: string - Name of the report template to use (optional - uses default template if not specified)
            output_name: string - Desired name of the generated report file (optional - auto-generated if not specified)

    Example Upload Mode: POST /api/v1/generatereport?template_name=Standard%20Report&output_name=report.pdf (with .vrd file in body)
    Example File Path Mode: POST /api/v1/generatereport
             Body: {"file_path": "test.vrd", "template_name": "Standard Report", "output_name": "report.pdf"}
             Or:   {"template_name": "Standard Report", "output_name": "report.pdf"} (uses last data file)
             Or:   POST /api/v1/generatereport (uses last data file, default template, and auto-generated filename)
             Or:   POST /api/v1/generatereport?template_name=Standard%20Report&output_name=report.pdf (query parameters)
    """
    content_type = request.content_type or ''

    # Check for file upload (multipart or raw binary)
    has_multipart_file = len(request.files) > 0
    has_binary_content = (
        request.content_length and request.content_length > 0 and
        not has_multipart_file and
        'application/json' not in content_type and
        'application/x-www-form-urlencoded' not in content_type
    )
    is_upload_mode = has_multipart_file or has_binary_content

    if is_upload_mode:
        # Upload Mode: Handle file upload with query parameters
        template_name = request.args.get('template_name')
        output_name = request.args.get('output_name')

        if not template_name:
            return jsonify(error_response(
                'Upload mode requires template_name query parameter',
                'MISSING_PARAMETER'
            )), 400

        if not output_name:
            return jsonify(error_response(
                'Upload mode requires output_name query parameter',
                'MISSING_PARAMETER'
            )), 400

        # Get file data from multipart or raw binary
        if has_multipart_file:
            file_field = next(iter(request.files))
            uploaded_file = request.files[file_field]
            binary_data = uploaded_file.read()
            content_length = len(binary_data)
        else:
            content_length = request.content_length
            binary_data = request.get_data()

        if content_length > MAX_CONTENT_LENGTH:
            return jsonify(error_response(
                'File too large (max 100MB)',
                'FILE_TOO_LARGE'
            )), 413

        # Validate output path security
        try:
            validated_output_path = validate_output_path(output_name, "report generation (upload)")
            output_name = os.path.basename(validated_output_path)
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'OUTPUT_PATH_VALIDATION_ERROR'
            )), 403

        try:

            # Create a temporary file for the uploaded .vrd data
            with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name

            try:
                # Generate report using the temporary file
                generated_file_path = GenerateReportFromVV(temp_file_path, template_name, output_name)
                file_path = temp_file_path  # For response data
                used_upload = True

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

        except Exception as e:
            return jsonify(error_response(
                f'Failed to upload and generate report: {str(e)}',
                'UPLOAD_REPORT_GENERATION_ERROR'
            )), 500

    else:
        # File Path Mode: Handle existing file with JSON body or query parameters
        try:
            request_data = request.get_json() or {}
        except Exception:
            request_data = {}

        file_path = request_data.get('file_path') or request.args.get('file_path')
        template_name = request_data.get('template_name') or request.args.get('template_name')
        output_name = request_data.get('output_name') or request.args.get('output_name')
        used_upload = False

        # If file_path is not provided, use the last data file from VibrationVIEW
        if not file_path:
            try:
                file_path = vv_instance.ReportField('LastDataFile')
                if not file_path:
                    return jsonify(error_response(
                        'No file_path provided and no last data file available in VibrationVIEW',
                        'NO_DATA_FILE_AVAILABLE'
                    )), 400
            except Exception as e:
                return jsonify(error_response(
                    f'Failed to get last data file from VibrationVIEW: {str(e)}',
                    'LAST_DATA_FILE_ERROR'
                )), 500

        # Use default template if not provided
        if not template_name:
            template_name = "Test Report.rtf"  # Default template

        # Use default output_name if not provided - base it on the data file name
        if not output_name:
            # Extract base filename from file_path and use template extension (same scheme as generatetxt)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            template_ext = os.path.splitext(template_name)[1]  # Get extension from template
            if template_ext:
                # Use template extension (e.g., .rtf, .pdf, .html)
                output_name = f"{base_name}{template_ext}"
            else:
                # Fallback to .pdf if template has no extension
                output_name = f"{base_name}.pdf"

        # Validate file_path security and existence
        try:
            validated_file_path = validate_file_path(file_path, "report generation")
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'PATH_VALIDATION_ERROR'
            )), 403

        if not os.path.exists(validated_file_path):
            return jsonify(error_response(
                f'File not found: {validated_file_path}',
                'FILE_NOT_FOUND'
            )), 404

        # Use validated path
        file_path = validated_file_path

        # Validate output path security
        try:
            validated_output_path = validate_output_path(output_name, "report generation")
            output_name = os.path.basename(validated_output_path)  # Use only filename for API call
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'OUTPUT_PATH_VALIDATION_ERROR'
            )), 403

        try:
            # Generate report
            generated_file_path = GenerateReportFromVV(file_path, template_name, output_name)

        except Exception as e:
            return jsonify(error_response(
                f'Failed to generate report: {str(e)}',
                'REPORT_GENERATION_ERROR'
            )), 500

    # Check if file was actually created
    if not os.path.exists(generated_file_path):
        return jsonify(error_response(
            f'Generated file does not exist at path: {generated_file_path}',
            'FILE_NOT_FOUND'
        )), 404

    return send_file(generated_file_path, as_attachment=True, download_name=os.path.basename(generated_file_path))


@report_generation_bp.route('/datafile', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def get_datafile(vv_instance):
    """
    Get Raw VibrationVIEW Data File

    Returns the unprocessed VibrationVIEW data file (.vrd) content.
    No report generation or format conversion is performed.

    Query Parameters:
        file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)

    Returns:
        Binary .vrd file content as base64-encoded data

    Example: GET /api/v1/datafile
             GET /api/v1/datafile?file_path=test.vrd
             POST /api/v1/datafile with JSON body: {"file_path": "test.vrd"}
    """
    try:
        request_data = request.get_json() or {}
    except Exception:
        request_data = {}

    file_path = request_data.get('file_path') or request.args.get('file_path')

    # If file_path is not provided, use the last data file from VibrationVIEW
    if not file_path:
        try:
            file_path = vv_instance.ReportField('LastDataFile')
            if not file_path:
                return jsonify(error_response(
                    'No file_path provided and no last data file available in VibrationVIEW',
                    'NO_DATA_FILE_AVAILABLE'
                )), 400
        except Exception as e:
            return jsonify(error_response(
                f'Failed to get last data file from VibrationVIEW: {str(e)}',
                'LAST_DATA_FILE_ERROR'
            )), 500

    # Validate file_path security and existence
    try:
        validated_file_path = validate_file_path(file_path, "datafile retrieval")
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'PATH_VALIDATION_ERROR'
        )), 403

    if not os.path.exists(validated_file_path):
        return jsonify(error_response(
            f'File not found: {validated_file_path}',
            'FILE_NOT_FOUND'
        )), 404

    return send_file(validated_file_path, as_attachment=True, download_name=os.path.basename(validated_file_path))


@report_generation_bp.route('/datafiles', methods=['GET'])
@handle_errors
@with_vibrationview
def get_datafiles(vv_instance):
    """
    Get All Data Files from most recently run test as Zip Archive

    Returns a zip file containing all data files from VibrationVIEW history
    using the ReportFieldsHistory method to get the list of files from most recent test.

    Returns:
        Zip archive containing all data files from history

    Example: GET /api/v1/datafiles
    """
    # Get the list of data files from VibrationVIEW history using ReportFieldsHistory
    try:
        # ReportFieldsHistory returns a 2D array: (parameter, value1, value2, ...)
        # Using 'LastData' to get the history of data files
        # if more than one data file, an additional row with LastData is always added to the top
        # when only one data file, it returns just fields without additional row
        fields_history = vv_instance.ReportFieldsHistory('LastData,StopCode,RunTime,Time')
        if not fields_history or len(fields_history) == 0:
            return jsonify(error_response(
                'No data files found in VibrationVIEW history',
                'NO_DATA_FILES'
            )), 404

        # Extract file paths from the history (skip first element which is the field name)
        # fields_history format: [['LastDataFile', 'file1.vrd', 'file2.vrd', ...]]
        file_paths = []
        for row in fields_history:
            # Skip the first element (field name) and collect file paths
            for file_path in row[1:]:
                if file_path and os.path.exists(file_path):
                    file_paths.append(file_path)

    except Exception as e:
        return jsonify(error_response(
            f'Failed to get data files from VibrationVIEW history: {str(e)}',
            'HISTORY_RETRIEVAL_ERROR'
        )), 500

    if not file_paths:
        return jsonify(error_response(
            'No valid data files found in VibrationVIEW history',
            'NO_FILES_FOUND'
        )), 404

    # Create zip file in memory
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        file_count = 0
        added_filenames = set()  # Track added filenames to avoid duplicates
        for file_path in file_paths:
            if os.path.isfile(file_path):
                filename = os.path.basename(file_path)
                # Handle duplicate filenames by adding a suffix
                original_filename = filename
                suffix = 1
                while filename in added_filenames:
                    name, ext = os.path.splitext(original_filename)
                    filename = f"{name}_{suffix}{ext}"
                    suffix += 1
                zip_file.write(file_path, filename)
                added_filenames.add(filename)
                file_count += 1

    if file_count == 0:
        return jsonify(error_response(
            'No files could be added to the archive',
            'NO_FILES_ADDED'
        )), 404

    zip_buffer.seek(0)

    # Generate zip filename based on first file's name (without path and extension)
    first_file_base = os.path.splitext(os.path.basename(file_paths[0]))[0]
    zip_filename = f'{first_file_base}.zip'

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_filename
    )


@report_generation_bp.route('/generatetxt', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def generate_txt(vv_instance):
    """
    Generate Text Files from VibrationVIEW Data

    Function: GenerateTXTFromVV(filePath, outputName)
    Converts VibrationVIEW data to text format using command line interface.
    Creates one text file per plot in the VibrationVIEW data file.

    Two modes of operation:
    1. File Upload Mode: POST with binary .vrd file in body and query parameters
    2. File Path Mode: POST with JSON body or query parameters specifying existing file path

    File Upload Mode:
        Query Parameters:
            output_name: string - Desired name of the generated text file (required for upload)
        Headers:
            Content-Length: Required for upload mode - File size in bytes (max 100MB)
            Content-Type: application/octet-stream (for binary upload)
        Body: Binary VibrationVIEW data file content (.vrd)

    File Path Mode:
        Request Body (JSON, optional) or Query Parameters:
            file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
            output_name: string - Base name for generated text files (optional - auto-generated if not specified)

    Note: Generates multiple files with pattern basename-1.txt, basename-2.txt, etc.
          where each file corresponds to a plot in the VibrationVIEW data file.
          Returns file content directly in response as text (TXT files are text-based).

    Example Upload Mode: POST /api/v1/generatetxt?output_name=data.txt (with .vrd file in body)
    Example File Path Mode: POST /api/v1/generatetxt
             Body: {"file_path": "test.vrd", "output_name": "data.txt"}
             Or:   {"output_name": "data.txt"} (uses last data file)
             Or:   POST /api/v1/generatetxt (uses last data file and auto-generated filename)
             Or:   POST /api/v1/generatetxt?output_name=data.txt (query parameters)
    """
    return _generate_files_common(vv_instance, 'TXT', GenerateTXTFromVV, 'text')


@report_generation_bp.route('/generateuff', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def generate_uff(vv_instance):
    """
    Generate UFF Files from VibrationVIEW Data

    Function: GenerateUFFFromVV(filePath, outputName)
    Converts VibrationVIEW data to Universal File Format using command line interface.
    Creates one UFF file per plot in the VibrationVIEW data file.

    Two modes of operation:
    1. File Upload Mode: POST with binary .vrd file in body and query parameters
    2. File Path Mode: POST with JSON body or query parameters specifying existing file path

    File Upload Mode:
        Query Parameters:
            output_name: string - Desired name of the generated UFF file (required for upload)
        Headers:
            Content-Length: Required for upload mode - File size in bytes (max 100MB)
            Content-Type: application/octet-stream (for binary upload)
        Body: Binary VibrationVIEW data file content (.vrd)

    File Path Mode:
        Request Body (JSON, optional) or Query Parameters:
            file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
            output_name: string - Base name for generated UFF files (optional - auto-generated if not specified)

    Note: Generates multiple files with pattern basename-1.uff, basename-2.uff, etc.
          where each file corresponds to a plot in the VibrationVIEW data file.
          Returns file content directly in response as text (UFF files are text-based).

    Example Upload Mode: POST /api/v1/generateuff?output_name=data.uff (with .vrd file in body)
    Example File Path Mode: POST /api/v1/generateuff
             Body: {"file_path": "test.vrd", "output_name": "data.uff"}
             Or:   {"output_name": "data.uff"} (uses last data file)
             Or:   POST /api/v1/generateuff (uses last data file and auto-generated filename)
             Or:   POST /api/v1/generateuff?output_name=data.uff (query parameters)
    """
    return _generate_files_common(vv_instance, 'UFF', GenerateUFFFromVV, 'UFF')


def _generate_files_common(vv_instance, file_type, generate_func, description):
    """
    Common implementation for generateuff and generatetxt endpoints

    Args:
        vv_instance: VibrationVIEW instance
        file_type: 'UFF' or 'TXT' for file type identification
        generate_func: The VibrationVIEW function to call (GenerateUFFFromVV or GenerateTXTFromVV)
        description: Description for error messages and responses

    Returns:
        Flask response with file generation results
    """
    extension = f'.{file_type.lower()}'
    content_type = request.content_type or ''

    # Check for file upload (multipart or raw binary)
    has_multipart_file = len(request.files) > 0
    has_binary_content = (
        request.content_length and request.content_length > 0 and
        not has_multipart_file and
        'application/json' not in content_type and
        'application/x-www-form-urlencoded' not in content_type
    )
    is_upload_mode = has_multipart_file or has_binary_content

    if is_upload_mode:
        # Upload Mode: Handle file upload with query parameters
        output_name = request.args.get('output_name')

        if not output_name:
            return jsonify(error_response(
                'Upload mode requires output_name query parameter',
                'MISSING_PARAMETER'
            )), 400

        # Get file data from multipart or raw binary
        if has_multipart_file:
            file_field = next(iter(request.files))
            uploaded_file = request.files[file_field]
            binary_data = uploaded_file.read()
            content_length = len(binary_data)
        else:
            content_length = request.content_length
            binary_data = request.get_data()

        if content_length > MAX_CONTENT_LENGTH:
            return jsonify(error_response(
                'File too large (max 100MB)',
                'FILE_TOO_LARGE'
            )), 413

        # Validate output path security
        try:
            validated_output_path = validate_output_path(output_name, "text generation (upload)")
            output_name = os.path.basename(validated_output_path)
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'OUTPUT_PATH_VALIDATION_ERROR'
            )), 403

        try:

            # Create a temporary file for the uploaded .vrd data
            with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
                temp_file.write(binary_data)
                temp_file_path = temp_file.name

            try:
                # Generate text file using the temporary file
                primary_file_path = generate_func(temp_file_path, output_name)
                file_path = temp_file_path  # For response data
                used_upload = True

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

        except Exception as e:
            return jsonify(error_response(
                f'Failed to upload and generate text file: {str(e)}',
                'UPLOAD_TXT_GENERATION_ERROR'
            )), 500

    else:
        # File Path Mode: Handle existing file with JSON body or query parameters
        try:
            request_data = request.get_json() or {}
        except Exception:
            request_data = {}

        file_path = request_data.get('file_path') or request.args.get('file_path')
        output_name = request_data.get('output_name') or request.args.get('output_name')
        used_upload = False

        # If file_path is not provided, use the last data file from VibrationVIEW
        if not file_path:
            try:
                file_path = vv_instance.ReportField('LastDataFile')
                if not file_path:
                    return jsonify(error_response(
                        'No file_path provided and no last data file available in VibrationVIEW',
                        'NO_DATA_FILE_AVAILABLE'
                    )), 400
            except Exception as e:
                return jsonify(error_response(
                    f'Failed to get last data file from VibrationVIEW: {str(e)}',
                    'LAST_DATA_FILE_ERROR'
                )), 500

        # Use default output_name if not provided - base it on the data file name
        if not output_name:
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_name = f"{base_name}{extension}"

        # Validate file_path security and existence
        try:
            validated_file_path = validate_file_path(file_path, "text generation")
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'PATH_VALIDATION_ERROR'
            )), 403

        if not os.path.exists(validated_file_path):
            return jsonify(error_response(
                f'File not found: {validated_file_path}',
                'FILE_NOT_FOUND'
            )), 404

        # Use validated path
        file_path = validated_file_path

        # Validate output path security
        try:
            validated_output_path = validate_output_path(output_name, "text generation")
            output_name = os.path.basename(validated_output_path)  # Use only filename for API call
        except PathValidationError as e:
            return jsonify(error_response(
                str(e),
                'OUTPUT_PATH_VALIDATION_ERROR'
            )), 403

        try:
            primary_file_path = generate_func(file_path, output_name)

        except Exception as e:
            return jsonify(error_response(
                f'Failed to generate text file: {str(e)}',
                'TXT_GENERATION_ERROR'
            )), 500

    # Find the first generated file (pattern: basename-1.ext)
    base_name = os.path.splitext(output_name)[0]
    directory = os.path.dirname(primary_file_path) if os.path.dirname(primary_file_path) else os.path.dirname(os.path.abspath(primary_file_path))

    # Check for first file with pattern: basename-1.ext
    first_file = os.path.join(directory, f"{base_name}-1{extension}")
    if os.path.exists(first_file):
        return send_file(first_file, as_attachment=True)

    # Fallback to primary file path if pattern file not found
    if os.path.exists(primary_file_path):
        return send_file(primary_file_path, as_attachment=True)

    return jsonify(error_response(
        f'Generated file not found',
        'FILE_NOT_FOUND'
    )), 404


# Constants for upload endpoints
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB limit for .vrd files
