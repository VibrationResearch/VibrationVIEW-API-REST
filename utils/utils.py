import os
import subprocess
import uuid

import logging
from vibrationviewapi import ExtractComErrorInfo
import config
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'vrp', 'vasor', 'vkp', 'vkd', 'vsp', 'vsd', 'vdp', 'vdd'}

def handle_binary_upload(filename, binary_data, uploadsubfolder='Uploads', usetemporaryfile=False):
    if not filename or '.' not in filename:
        return None, {'Error': 'Missing or invalid filename'}, 400

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None, {'Error': f'Invalid file extension: .{ext}'}, 400

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