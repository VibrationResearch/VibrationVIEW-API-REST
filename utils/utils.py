import os
import subprocess
import uuid
import math

import logging
from flask import request
from urllib.parse import unquote
from vibrationviewapi import ExtractComErrorInfo
import config
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'vrp', 'vrpj', 'vasor', 'vkp', 'vkpj', 'vkd', 'vsp', 'vspj', 'vsd', 'vdp', 'vdpj', 'vdd', 
                     'vsyscheckt', 'vsinet', 'vrandomt', 'vsort', 'vrort', 'vsorort', 
                     'vsost', 'vanalyzert', 'vshockt', 'vudtt', 'vsrst', 'vtransientt', 'vic', 'vchan'}

TEMPLATE_EXTENSIONS = {'vsyscheckt', 'vsinet', 'vrandomt', 'vsort', 'vrort', 'vsorort', 
                      'vsost', 'vanalyzert', 'vshockt', 'vudtt', 'vsrst', 'vtransientt'}

def handle_binary_upload(filename, binary_data, uploadsubfolder='Uploads', usetemporaryfile=False):
    if not filename or '.' not in filename:
        return None, {'Error': 'Missing or invalid filename'}, 400

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, {'Error': f'Invalid file extension: .{ext}'}, 400

    # Check if uploadsubfolder is an absolute path (for template files)
    if os.path.isabs(uploadsubfolder):
        temp_folder = uploadsubfolder
    else:
        temp_folder = os.path.join(config.Config.PROFILE_FOLDER, uploadsubfolder)
    
    os.makedirs(temp_folder, exist_ok=True)

    if usetemporaryfile:
        unique_id = uuid.uuid4().hex
        base, ext = os.path.splitext(filename)
        filename = f'{base}_{unique_id}{ext}'

    safe_filename = secure_filename(filename)
    safe_filename = safe_filename.lstrip('/\\')
    file_path = os.path.join(temp_folder, safe_filename)

    with open(file_path, 'wb') as f:
        f.write(binary_data)

    logging.info(f"Binary file saved: {file_path}")

    return {
        'FilePath': file_path,
        'Filename': filename,
        'Size': os.path.getsize(file_path)
    }, None, 200

def ParseVvTable(tsv_text: str):
    try:
        lines = tsv_text.strip().splitlines()
        if len(lines) < 2:
            return [{'RawText': tsv_text}]

        headers = lines[0].split('\t')
        data = []

        for line in lines[1:]:
            values = line.split('\t')
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))
            else:
                print(f'Skipping malformed line: {line}')

        return data

    except Exception as e:
        return [{'Error': f'Error parsing TSV: {e}'}]

def DecodeStatusColor(status):
    color_map = {
        0: 'healthy',
        1: 'yellow',
        2: 'critical'
    }
        # Convert string to integer if needed

    return_color_code = status['stop_code_index'] >> 12
    return color_map.get(return_color_code, 'unknown')


def get_channel_data(vv_instance, field_keys):
    """
    Common function to get channel data for multiple routes
    
    Args:
        vv_instance: VibrationVIEW instance
        field_keys: List of field keys to retrieve for each channel
        
    Returns:
        List of dictionaries with channel data
    """
    if not vv_instance:
        return None
        
    channel_count = vv_instance.GetHardwareInputChannels()
    
    # Collect all fields per channel
    field_data = {
        key: [vv_instance.ReportField(f'{key}{i + 1}') for i in range(channel_count)]
        for key in field_keys
    }

    # Combine into list of dictionaries per channel
    channels = []
    for i in range(channel_count):
        channel_info = {
            key: field_data[key][i] for key in field_keys
        }
        channels.append(channel_info)
        
    return channels

def GenerateReportFromVV(filePath: str, templateName: str, outputName: str) -> str:
    """
    Runs the external report generator,
    and returns the path to the generated report.

    Args:
        filePath (str): The VV filename
        templateName (str): Name of the report template to use
        outputName (str): Desired name of the generated report file

    Returns:
        str: Path to the generated report file
    """

    # Prepare report output directory
    reportFolder = os.path.join(config.REPORT_FOLDER, 'Temporary')
    os.makedirs(reportFolder, exist_ok=True)

    outPath = os.path.join(reportFolder, outputName)

    # Build and run report generation command
    command = [
        config.EXE_NAME,
        '/savereport', filePath,
        '/template', templateName,
        '/output', outPath
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f'Report generation failed.\nCommand: {" ".join(command)}\nStderr: {result.stderr.strip()}'
        )

    return outPath

def GetVectorData(vvInstance,vector):
    try:
        cols = vvInstance.GetHardwareInputChannels() + 1
        dataList = []
        dataList.append(vvInstance.Vector(vector))

        headers = [vvInstance.VectorLabel(vector)]
        for i in range(cols - 1):
            field = f'CH{i+1}NAME'
            headers.append(vvInstance.ReportField(field))
            dataList.append(vvInstance.Vector(vector + i))

        units = [vvInstance.VectorUnit(vector + i) for i in range(cols)]

        return {'headers': headers, 'units': units, 'columns': dataList}

    except Exception as e:
        raise RuntimeError(f'Error retrieving vector data: {e}')

def extract_com_error_info(exception):
    """
    Extract information from COM errors for better error reporting
    This is a wrapper for ExtractComErrorInfo to ensure consistent error handling
    """
    try:
        return ExtractComErrorInfo(exception)
    except Exception:
        # Fallback if ExtractComErrorInfo fails
        return str(exception)

def convert_channel_to_com_index(channel_user):
    """
    Convert user-provided 1-based channel number to 0-based COM index
    
    Args:
        channel_user: User-provided channel number (1-based)
        
    Returns:
        tuple: (channel_com, error_response, status_code)
               - channel_com: 0-based channel for COM calls (None if error)
               - error_response: Error dict if invalid (None if valid)
               - status_code: HTTP status code if error (None if valid)
    """
    try:
        channel = int(channel_user)
        if channel < 1:
            from utils.response_helpers import error_response
            return None, error_response(
                'Channel parameter must be >= 1',
                'INVALID_PARAMETER'
            ), 400
        return channel - 1, None, None
    except (ValueError, TypeError):
        from utils.response_helpers import error_response
        return None, error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        ), 400

def is_template_file(filename):
    """
    Check if a file has a template extension
    
    Args:
        filename: The filename to check
        
    Returns:
        bool: True if the file is a template file, False otherwise
    """
    if not filename or '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in TEMPLATE_EXTENSIONS

def get_new_test_defaults_path():
    """
    Get the New Test Defaults folder path from configuration
    
    Returns:
        str: Path to the New Test Defaults folder
    """
    return config.Config.NEW_TEST_DEFAULTS_FOLDER

# Pre-computed lowercase default template filenames for performance
DEFAULT_TEMPLATE_FILENAMES = {
    'random.vrandomt',
    'sine.vsinet', 
    'shock.vshockt',
    'fdr.vfdrt',
    'sor.vsort',
    'sos.vsost',
    'ror.vrort',
    'sororor.vsorort',
    'srs.vsrst',
    'user-defined transient.vudtt',
    'transient.vtransientt',
    'analyzer.vanalyzert'
}

def is_default_template_filename(filename):
    """
    Check if filename matches one of the default VibrationVIEW template files
    that should be copied but not opened with automation command

    Args:
        filename: The filename to check

    Returns:
        bool: True if filename matches a default template, False otherwise
    """
    return filename.lower() in DEFAULT_TEMPLATE_FILENAMES


def sanitize_nan(value):
    """
    Replace NaN and Inf float values with None for JSON serialization.

    Args:
        value: A value that may be a float NaN/Inf, list, tuple, or other type

    Returns:
        The value with NaN/Inf replaced by None, recursively for lists/tuples
    """
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, (list, tuple)):
        return [sanitize_nan(v) for v in value]
    return value


# Maximum file upload size (10 MB)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024


def detect_file_upload():
    """
    Detect if the current request contains a file upload.

    Returns:
        tuple: (filename, binary_data, content_length) if file upload detected
        tuple: (None, None, None) if no file upload
        tuple: (error_response, status_code, None) if error occurred

    Supports:
        - multipart/form-data with any file field name
        - Raw binary body with filename in query parameter
    """
    content_type = request.content_type or ''

    logging.debug(f"detect_file_upload: method={request.method}, content_type={content_type}, "
                  f"content_length={request.content_length}, files={list(request.files.keys())}")

    # Check for multipart file upload (any field name)
    has_multipart_file = len(request.files) > 0

    # Check for raw binary upload (exclude json, form, multipart)
    is_binary_content_type = (
        request.content_length and request.content_length > 0 and
        not has_multipart_file and
        'multipart' not in content_type and
        'application/json' not in content_type and
        'application/x-www-form-urlencoded' not in content_type
    )

    if has_multipart_file:
        # Multipart/form-data mode - get first file from any field name
        file_field = next(iter(request.files))
        uploaded_file = request.files[file_field]
        filename = uploaded_file.filename
        binary_data = uploaded_file.read()
        content_length = len(binary_data)
        logging.debug(f"detect_file_upload: multipart file field={file_field}, filename={filename}, size={content_length}")

        if not filename:
            return ({'Error': 'Multipart file field has no filename'}, 400, None)

        if content_length > MAX_UPLOAD_SIZE:
            return ({'Error': 'File too large (max 10MB)'}, 413, None)

        return (filename, binary_data, content_length)

    elif is_binary_content_type:
        # Raw binary mode - get filename from query parameter
        filename = request.args.get("filename")

        if filename is None:
            query_string = request.query_string.decode('utf-8')
            if query_string:
                filename = unquote(query_string)

        if not filename:
            return ({'Error': 'Missing filename: provide via multipart/form-data file field or query parameter'}, 400, None)

        content_length = request.content_length

        if content_length > MAX_UPLOAD_SIZE:
            return ({'Error': 'File too large (max 10MB)'}, 413, None)

        binary_data = request.get_data()
        logging.debug(f"detect_file_upload: raw binary filename={filename}, size={content_length}")

        return (filename, binary_data, content_length)

    # No file upload detected
    return (None, None, None)


def get_filename_from_request():
    """
    Extract filename from request query parameters.

    Returns:
        str: The filename, or None if not found
    """
    filename = request.args.get("filename")

    if filename is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            filename = unquote(query_string)

    return filename