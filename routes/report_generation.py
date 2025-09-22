# ============================================================================
# FILE: routes/report_generation.py (Report Generation Routes) - v1
# ============================================================================

"""
Report Generation Routes - VibrationVIEW Command Line Operations
File generation operations using VibrationVIEW command line interface
"""

from flask import Blueprint, request, jsonify
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.vv_manager import with_vibrationview
from utils.path_validator import validate_file_path, validate_output_path, PathValidationError
from vibrationviewapi import GenerateReportFromVV, GenerateTXTFromVV, GenerateUFFFromVV
import logging
import os
import tempfile

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
                'description': 'Generate a report file from VibrationVIEW data using a template and return content to client',
                'function': 'GenerateReportFromVV(filePath, templateName, outputName)',
                'parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'template_name': 'string - Name of the report template to use (optional - uses "Test Report.rtf" if not specified)',
                    'output_name': 'string - Desired name of the generated report file (optional - auto-generated with same extension as template_name if not specified)'
                },
                'returns': 'object - Success status, path to generated report file, and file content (text or base64-encoded binary)',
                'note': 'Returns file content directly in response. Text files (HTML, TXT, CSV) returned as text, binary files (PDF, DOC) returned as base64',
                'example': 'POST /api/generatereport (no body required) or with JSON body: {"file_path": "test.vrd", "template_name": "Standard Report", "output_name": "report.pdf"} or query params: ?template_name=Standard%20Report&output_name=report.pdf'
            },
            'POST /generatetxt': {
                'description': 'Generate text files from VibrationVIEW data - creates one file per plot in the datafile',
                'function': 'GenerateTXTFromVV(filePath, outputName)',
                'parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'output_name': 'string - Base name for generated text files (optional - auto-generated if not specified)'
                },
                'returns': 'object - Success status, paths to all generated text files (basename-1.txt, basename-2.txt, etc.), and combined file contents',
                'note': 'Creates multiple files with pattern basename-N.txt where N corresponds to each plot in the VibrationVIEW data file',
                'example': 'POST /api/generatetxt (no body required) or with JSON body: {"file_path": "test.vrd", "output_name": "data.txt"} or query params: ?output_name=data.txt'
            },
            'POST /generateuff': {
                'description': 'Generate UFF (Universal File Format) files from VibrationVIEW data - creates one file per plot in the datafile',
                'function': 'GenerateUFFFromVV(filePath, outputName)',
                'parameters': {
                    'file_path': 'string - Path to VibrationVIEW data file (optional - uses last data file if not specified)',
                    'output_name': 'string - Base name for generated UFF files (optional - auto-generated with .uff extension if not specified)'
                },
                'returns': 'object - Success status, paths to all generated UFF files (basename-1.uff, basename-2.uff, etc.), and combined file contents',
                'note': 'Creates multiple files with pattern basename-N.uff where N corresponds to each plot in the VibrationVIEW data file',
                'example': 'POST /api/generateuff (no body required) or with JSON body: {"file_path": "test.vrd", "output_name": "data.uff"} or query params: ?output_name=data.uff'
            },
            'PUT /generatereport': {
                'description': 'Upload VibrationVIEW data file and generate a report using a template',
                'function': 'GenerateReportFromVV(filePath, templateName, outputName)',
                'parameters': {
                    'template_name': 'string - Query parameter with report template name (required)',
                    'output_name': 'string - Query parameter with desired output filename (required)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)'
                },
                'headers': {
                    'Content-Length': 'required - File size in bytes'
                },
                'returns': 'object - Success status and path to generated report file',
                'example': 'PUT /api/generatereport?template_name=Standard%20Report&output_name=report.pdf (with .vrd file in body)'
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
                'example': 'PUT /api/generatetxt?output_name=data.txt (with .vrd file in body)'
            },
            'PUT /generateuff': {
                'description': 'Upload VibrationVIEW data file and generate a UFF file',
                'function': 'GenerateUFFFromVV(filePath, outputName)',
                'parameters': {
                    'output_name': 'string - Query parameter with desired output filename (required)',
                    'body': 'binary - VibrationVIEW data file content (.vrd)'
                },
                'headers': {
                    'Content-Length': 'required - File size in bytes'
                },
                'returns': 'object - Success status and path to generated UFF file',
                'example': 'PUT /api/generateuff?output_name=data.uff (with .vrd file in body)'
            }
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
            'PUT endpoints accept file uploads in the request body',
            'If file_path is not provided in POST requests, uses VibrationVIEW.GetReportField("LastDataFile")'
        ]
    }
    return jsonify(docs)


@report_generation_bp.route('/generatereport', methods=['POST'])
@handle_errors
@with_vibrationview
def generate_report(vv_instance):
    """
    Generate Report File from VibrationVIEW Data

    Function: GenerateReportFromVV(filePath, templateName, outputName)
    Generates a report file using VibrationVIEW command line interface
    with the specified template.

    Request Body (JSON, optional) or Query Parameters:
        file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
        template_name: string - Name of the report template to use (optional - uses default template if not specified)
        output_name: string - Desired name of the generated report file (optional - auto-generated if not specified)

    Example: POST /api/generatereport
             Body: {"file_path": "test.vrd", "template_name": "Standard Report", "output_name": "report.pdf"}
             Or:   {"template_name": "Standard Report", "output_name": "report.pdf"} (uses last data file)
             Or:   POST /api/generatereport (uses last data file, default template, and auto-generated filename)
             Or:   POST /api/generatereport?template_name=Standard%20Report&output_name=report.pdf (query parameters)
    """
    # Get parameters from JSON body (optional) or query parameters
    try:
        request_data = request.get_json() or {}
    except Exception:
        # If JSON parsing fails, use empty dict and fall back to query parameters
        request_data = {}

    file_path = request_data.get('file_path') or request.args.get('file_path')
    template_name = request_data.get('template_name') or request.args.get('template_name')
    output_name = request_data.get('output_name') or request.args.get('output_name')

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

        # Check if file was actually created
        file_exists = os.path.exists(generated_file_path)
        file_size = os.path.getsize(generated_file_path) if file_exists else 0

        # Read the generated report file content (if it's a readable format)
        file_content = ""
        content_error = None
        content_type = "unknown"
        is_binary = False

        if file_exists:
            if file_size > 0:
                # Determine file type from extension
                file_ext = os.path.splitext(generated_file_path)[1].lower()

                if file_ext in ['.txt', '.html', '.htm', '.xml', '.csv']:
                    # Text-based formats - read as text
                    content_type = "text"
                    try:
                        with open(generated_file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(generated_file_path, 'r', encoding='latin-1') as f:
                                file_content = f.read()
                        except Exception as e:
                            content_error = f"Failed to read text file: {str(e)}"
                    except Exception as e:
                        content_error = f"Failed to read file: {str(e)}"

                elif file_ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
                    # Binary formats - read as base64
                    content_type = "binary"
                    is_binary = True
                    try:
                        import base64
                        with open(generated_file_path, 'rb') as f:
                            binary_data = f.read()
                            file_content = base64.b64encode(binary_data).decode('utf-8')
                    except Exception as e:
                        content_error = f"Failed to read binary file: {str(e)}"

                else:
                    # Unknown format - try as text first, then binary
                    try:
                        with open(generated_file_path, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                            content_type = "text"
                    except:
                        try:
                            import base64
                            with open(generated_file_path, 'rb') as f:
                                binary_data = f.read()
                                file_content = base64.b64encode(binary_data).decode('utf-8')
                                content_type = "binary"
                                is_binary = True
                        except Exception as e:
                            content_error = f"Failed to read file as text or binary: {str(e)}"
            else:
                content_error = "Generated file is empty (0 bytes)"
        else:
            content_error = f"Generated file does not exist at path: {generated_file_path}"

        response_data = {
            'generated_file_path': generated_file_path,
            'file_path': file_path,
            'template_name': template_name,
            'output_name': output_name,
            'used_last_data_file': 'file_path' not in request_data,
            'file_exists': file_exists,
            'file_size': file_size,
            'content_type': content_type,
            'is_binary': is_binary,
            'content': file_content
        }

        # Add content error info if there was an issue
        if content_error:
            response_data['content_error'] = content_error

        return jsonify(success_response(
            response_data,
            f"Report generated: {generated_file_path}" + (f" (Warning: {content_error})" if content_error else "")
        ))

    except Exception as e:
        return jsonify(error_response(
            f'Failed to generate report: {str(e)}',
            'REPORT_GENERATION_ERROR'
        )), 500


@report_generation_bp.route('/generatetxt', methods=['POST'])
@handle_errors
@with_vibrationview
def generate_txt(vv_instance):
    """
    Generate Text Files from VibrationVIEW Data

    Function: GenerateTXTFromVV(filePath, outputName)
    Converts VibrationVIEW data to text format using command line interface.
    Creates one text file per plot in the VibrationVIEW data file.

    Request Body (JSON, optional) or Query Parameters:
        file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
        output_name: string - Base name for generated text files (optional - auto-generated if not specified)

    Note: Generates multiple files with pattern basename-1.txt, basename-2.txt, etc.
          where each file corresponds to a plot in the VibrationVIEW data file.

    Example: POST /api/generatetxt
             Body: {"file_path": "test.vrd", "output_name": "data.txt"}
             Or:   {"output_name": "data.txt"} (uses last data file)
             Or:   POST /api/generatetxt (uses last data file and auto-generated filename)
             Or:   POST /api/generatetxt?output_name=data.txt (query parameters)
    """
    # Get parameters from JSON body (optional) or query parameters
    try:
        request_data = request.get_json() or {}
    except Exception:
        # If JSON parsing fails, use empty dict and fall back to query parameters
        request_data = {}

    file_path = request_data.get('file_path') or request.args.get('file_path')
    output_name = request_data.get('output_name') or request.args.get('output_name')

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
        # Extract base filename from file_path and change extension to .txt
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_name = f"{base_name}.txt"

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
        # Generate text files (may create multiple files)
        primary_file_path = GenerateTXTFromVV(file_path, output_name)

        # Find all generated files matching the pattern outputfilename-n.txt (n=1-9)
        base_name = os.path.splitext(output_name)[0]  # Remove .txt extension
        directory = os.path.dirname(primary_file_path) if os.path.dirname(primary_file_path) else os.path.dirname(os.path.abspath(primary_file_path))

        generated_files = []
        all_content = ""

        # Check for files with pattern: basename-1.txt, basename-2.txt, etc.
        for i in range(1, 10):  # Check files 1-9
            pattern_file = os.path.join(directory, f"{base_name}-{i}.txt")
            if os.path.exists(pattern_file):
                file_size = os.path.getsize(pattern_file)
                file_content = ""

                # Read file content
                if file_size > 0:
                    try:
                        with open(pattern_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(pattern_file, 'r', encoding='latin-1') as f:
                                file_content = f.read()
                        except Exception as e:
                            file_content = f"[Error reading file: {str(e)}]"
                    except Exception as e:
                        file_content = f"[Error reading file: {str(e)}]"

                generated_files.append({
                    'file_path': pattern_file,
                    'file_name': f"{base_name}-{i}.txt",
                    'file_size': file_size,
                    'content': file_content
                })

                # Append to combined content with separator
                if all_content:
                    all_content += f"\n\n--- File {i}: {base_name}-{i}.txt ---\n\n"
                else:
                    all_content += f"--- File {i}: {base_name}-{i}.txt ---\n\n"
                all_content += file_content

        # If no pattern files found, check the original file path
        if not generated_files and os.path.exists(primary_file_path):
            file_size = os.path.getsize(primary_file_path)
            file_content = ""

            if file_size > 0:
                try:
                    with open(primary_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(primary_file_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    except Exception as e:
                        file_content = f"[Error reading file: {str(e)}]"
                except Exception as e:
                    file_content = f"[Error reading file: {str(e)}]"

            generated_files.append({
                'file_path': primary_file_path,
                'file_name': output_name,
                'file_size': file_size,
                'content': file_content
            })
            all_content = file_content

        response_data = {
            'primary_file_path': primary_file_path,
            'file_path': file_path,
            'output_name': output_name,
            'used_last_data_file': 'file_path' not in request_data,
            'files_found': len(generated_files),
            'generated_files': generated_files,
            'combined_content': all_content,
            'total_size': sum(f['file_size'] for f in generated_files)
        }

        return jsonify(success_response(
            response_data,
            f"Text file(s) generated successfully. Found {len(generated_files)} file(s)."
        ))

    except Exception as e:
        return jsonify(error_response(
            f'Failed to generate text file: {str(e)}',
            'TXT_GENERATION_ERROR'
        )), 500


@report_generation_bp.route('/generateuff', methods=['POST'])
@handle_errors
@with_vibrationview
def generate_uff(vv_instance):
    """
    Generate UFF Files from VibrationVIEW Data

    Function: GenerateUFFFromVV(filePath, outputName)
    Converts VibrationVIEW data to Universal File Format using command line interface.
    Creates one UFF file per plot in the VibrationVIEW data file.

    Request Body (JSON, optional) or Query Parameters:
        file_path: string - Path to VibrationVIEW data file (optional - uses last data file if not specified)
        output_name: string - Base name for generated UFF files (optional - auto-generated if not specified)

    Note: Generates multiple files with pattern basename-1.uff, basename-2.uff, etc.
          where each file corresponds to a plot in the VibrationVIEW data file.

    Example: POST /api/generateuff
             Body: {"file_path": "test.vrd", "output_name": "data.uff"}
             Or:   {"output_name": "data.uff"} (uses last data file)
             Or:   POST /api/generateuff (uses last data file and auto-generated filename)
             Or:   POST /api/generateuff?output_name=data.uff (query parameters)
    """
    # Get parameters from JSON body (optional) or query parameters
    try:
        request_data = request.get_json() or {}
    except Exception:
        # If JSON parsing fails, use empty dict and fall back to query parameters
        request_data = {}

    file_path = request_data.get('file_path') or request.args.get('file_path')
    output_name = request_data.get('output_name') or request.args.get('output_name')

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
        # Extract base filename from file_path and change extension to .uff
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_name = f"{base_name}.uff"

    # Validate file_path security and existence
    try:
        validated_file_path = validate_file_path(file_path, "UFF generation")
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
        validated_output_path = validate_output_path(output_name, "UFF generation")
        output_name = os.path.basename(validated_output_path)  # Use only filename for API call
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'OUTPUT_PATH_VALIDATION_ERROR'
        )), 403

    try:
        # Generate UFF files (may create multiple files)
        primary_file_path = GenerateUFFFromVV(file_path, output_name)

        # Find all generated files matching the pattern outputfilename-n.uff (n=1-9)
        base_name = os.path.splitext(output_name)[0]  # Remove .uff extension
        directory = os.path.dirname(primary_file_path) if os.path.dirname(primary_file_path) else os.path.dirname(os.path.abspath(primary_file_path))

        generated_files = []
        all_content = ""

        # Check for files with pattern: basename-1.uff, basename-2.uff, etc.
        for i in range(1, 10):  # Check files 1-9
            pattern_file = os.path.join(directory, f"{base_name}-{i}.uff")
            if os.path.exists(pattern_file):
                file_size = os.path.getsize(pattern_file)
                file_content = ""

                # Read file content (UFF files are text-based)
                if file_size > 0:
                    try:
                        with open(pattern_file, 'r', encoding='utf-8') as f:
                            file_content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(pattern_file, 'r', encoding='latin-1') as f:
                                file_content = f.read()
                        except Exception as e:
                            file_content = f"[Error reading file: {str(e)}]"
                    except Exception as e:
                        file_content = f"[Error reading file: {str(e)}]"

                generated_files.append({
                    'file_path': pattern_file,
                    'file_name': f"{base_name}-{i}.uff",
                    'file_size': file_size,
                    'content': file_content
                })

                # Append to combined content with separator
                if all_content:
                    all_content += f"\n\n--- File {i}: {base_name}-{i}.uff ---\n\n"
                else:
                    all_content += f"--- File {i}: {base_name}-{i}.uff ---\n\n"
                all_content += file_content

        # If no pattern files found, check the original file path
        if not generated_files and os.path.exists(primary_file_path):
            file_size = os.path.getsize(primary_file_path)
            file_content = ""

            if file_size > 0:
                try:
                    with open(primary_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    try:
                        with open(primary_file_path, 'r', encoding='latin-1') as f:
                            file_content = f.read()
                    except Exception as e:
                        file_content = f"[Error reading file: {str(e)}]"
                except Exception as e:
                    file_content = f"[Error reading file: {str(e)}]"

            generated_files.append({
                'file_path': primary_file_path,
                'file_name': output_name,
                'file_size': file_size,
                'content': file_content
            })
            all_content = file_content

        response_data = {
            'primary_file_path': primary_file_path,
            'file_path': file_path,
            'output_name': output_name,
            'used_last_data_file': 'file_path' not in request_data,
            'files_found': len(generated_files),
            'generated_files': generated_files,
            'combined_content': all_content,
            'total_size': sum(f['file_size'] for f in generated_files)
        }

        return jsonify(success_response(
            response_data,
            f"UFF file(s) generated successfully. Found {len(generated_files)} file(s)."
        ))

    except Exception as e:
        return jsonify(error_response(
            f'Failed to generate UFF file: {str(e)}',
            'UFF_GENERATION_ERROR'
        )), 500


# Constants for upload endpoints
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB limit for .vrd files


@report_generation_bp.route('/generatereport', methods=['PUT'])
@handle_errors
def upload_and_generate_report():
    """
    Upload VibrationVIEW Data File and Generate Report

    Function: GenerateReportFromVV(filePath, templateName, outputName)
    Uploads a VibrationVIEW data file and generates a report using the specified template.

    Query Parameters:
        template_name: string - Name of the report template to use
        output_name: string - Desired name of the generated report file

    Headers:
        Content-Length: Required - File size in bytes (max 100MB)

    Body:
        Binary VibrationVIEW data file content (.vrd)

    Example: PUT /api/generatereport?template_name=Standard%20Report&output_name=report.pdf
    """
    # Get parameters from query string
    template_name = request.args.get('template_name')
    output_name = request.args.get('output_name')
    content_length = request.content_length

    if not template_name:
        return jsonify(error_response(
            'Missing required query parameter: template_name',
            'MISSING_PARAMETER'
        )), 400

    if not output_name:
        return jsonify(error_response(
            'Missing required query parameter: output_name',
            'MISSING_PARAMETER'
        )), 400

    # Validate output path security
    try:
        validated_output_path = validate_output_path(output_name, "report generation (upload)")
        output_name = os.path.basename(validated_output_path)  # Use only filename for API call
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'OUTPUT_PATH_VALIDATION_ERROR'
        )), 403

    if content_length is None:
        return jsonify(error_response(
            'Missing Content-Length header',
            'MISSING_HEADER'
        )), 411  # Length Required

    if content_length > MAX_CONTENT_LENGTH:
        return jsonify(error_response(
            'File too large (max 100MB)',
            'FILE_TOO_LARGE'
        )), 413  # Payload Too Large

    try:
        # Get the uploaded file data
        binary_data = request.get_data()

        # Create a temporary file for the uploaded .vrd data
        with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
            temp_file.write(binary_data)
            temp_file_path = temp_file.name

        try:
            # Generate report using the temporary file
            generated_file_path = GenerateReportFromVV(temp_file_path, template_name, output_name)

            return jsonify(success_response(
                {
                    'generated_file_path': generated_file_path,
                    'template_name': template_name,
                    'output_name': output_name,
                    'uploaded_file_size': content_length,
                    'file_exists': os.path.exists(generated_file_path),
                    'file_size': os.path.getsize(generated_file_path) if os.path.exists(generated_file_path) else 0
                },
                f"Report generated successfully from uploaded file: {generated_file_path}"
            ))

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


@report_generation_bp.route('/generatetxt', methods=['PUT'])
@handle_errors
def upload_and_generate_txt():
    """
    Upload VibrationVIEW Data File and Generate Text File

    Function: GenerateTXTFromVV(filePath, outputName)
    Uploads a VibrationVIEW data file and converts it to text format.

    Query Parameters:
        output_name: string - Desired name of the generated text file

    Headers:
        Content-Length: Required - File size in bytes (max 100MB)

    Body:
        Binary VibrationVIEW data file content (.vrd)

    Example: PUT /api/generatetxt?output_name=data.txt
    """
    # Get parameters from query string
    output_name = request.args.get('output_name')
    content_length = request.content_length

    if not output_name:
        return jsonify(error_response(
            'Missing required query parameter: output_name',
            'MISSING_PARAMETER'
        )), 400

    # Validate output path security
    try:
        validated_output_path = validate_output_path(output_name, "text generation (upload)")
        output_name = os.path.basename(validated_output_path)  # Use only filename for API call
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'OUTPUT_PATH_VALIDATION_ERROR'
        )), 403

    if content_length is None:
        return jsonify(error_response(
            'Missing Content-Length header',
            'MISSING_HEADER'
        )), 411  # Length Required

    if content_length > MAX_CONTENT_LENGTH:
        return jsonify(error_response(
            'File too large (max 100MB)',
            'FILE_TOO_LARGE'
        )), 413  # Payload Too Large

    try:
        # Get the uploaded file data
        binary_data = request.get_data()

        # Create a temporary file for the uploaded .vrd data
        with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
            temp_file.write(binary_data)
            temp_file_path = temp_file.name

        try:
            # Generate text file using the temporary file
            generated_file_path = GenerateTXTFromVV(temp_file_path, output_name)

            # Read the generated text file content
            file_content = ""
            if os.path.exists(generated_file_path):
                try:
                    with open(generated_file_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except UnicodeDecodeError:
                    # Try with different encoding if UTF-8 fails
                    with open(generated_file_path, 'r', encoding='latin-1') as f:
                        file_content = f.read()

            return jsonify(success_response(
                {
                    'generated_file_path': generated_file_path,
                    'output_name': output_name,
                    'uploaded_file_size': content_length,
                    'file_exists': os.path.exists(generated_file_path),
                    'file_size': os.path.getsize(generated_file_path) if os.path.exists(generated_file_path) else 0,
                    'content': file_content
                },
                f"Text file generated successfully from uploaded file: {generated_file_path}"
            ))

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


@report_generation_bp.route('/generateuff', methods=['PUT'])
@handle_errors
def upload_and_generate_uff():
    """
    Upload VibrationVIEW Data File and Generate UFF File

    Function: GenerateUFFFromVV(filePath, outputName)
    Uploads a VibrationVIEW data file and converts it to Universal File Format.

    Query Parameters:
        output_name: string - Desired name of the generated UFF file

    Headers:
        Content-Length: Required - File size in bytes (max 100MB)

    Body:
        Binary VibrationVIEW data file content (.vrd)

    Example: PUT /api/generateuff?output_name=data.uff
    """
    # Get parameters from query string
    output_name = request.args.get('output_name')
    content_length = request.content_length

    if not output_name:
        return jsonify(error_response(
            'Missing required query parameter: output_name',
            'MISSING_PARAMETER'
        )), 400

    # Validate output path security
    try:
        validated_output_path = validate_output_path(output_name, "UFF generation (upload)")
        output_name = os.path.basename(validated_output_path)  # Use only filename for API call
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'OUTPUT_PATH_VALIDATION_ERROR'
        )), 403

    if content_length is None:
        return jsonify(error_response(
            'Missing Content-Length header',
            'MISSING_HEADER'
        )), 411  # Length Required

    if content_length > MAX_CONTENT_LENGTH:
        return jsonify(error_response(
            'File too large (max 100MB)',
            'FILE_TOO_LARGE'
        )), 413  # Payload Too Large

    try:
        # Get the uploaded file data
        binary_data = request.get_data()

        # Create a temporary file for the uploaded .vrd data
        with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
            temp_file.write(binary_data)
            temp_file_path = temp_file.name

        try:
            # Generate UFF file using the temporary file
            generated_file_path = GenerateUFFFromVV(temp_file_path, output_name)

            return jsonify(success_response(
                {
                    'generated_file_path': generated_file_path,
                    'output_name': output_name,
                    'uploaded_file_size': content_length,
                    'file_exists': os.path.exists(generated_file_path),
                    'file_size': os.path.getsize(generated_file_path) if os.path.exists(generated_file_path) else 0
                },
                f"UFF file generated successfully from uploaded file: {generated_file_path}"
            ))

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {temp_file_path}: {cleanup_error}")

    except Exception as e:
        return jsonify(error_response(
            f'Failed to upload and generate UFF file: {str(e)}',
            'UPLOAD_UFF_GENERATION_ERROR'
        )), 500