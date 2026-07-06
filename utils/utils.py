import logging
import os
import re
import subprocess
import sys
import threading
import uuid
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote

from flask import request
from werkzeug.utils import secure_filename

from config import Config
from utils.exceptions import APIError
from utils.response_helpers import error_response

logger = logging.getLogger(__name__)


def get_system_info() -> Dict[str, Any]:
    """Return a dict of Python runtime diagnostics for diagnostic endpoints."""
    return {
        "python_version": sys.version,
        "python_architecture": "64-bit" if sys.maxsize > 2**32 else "32-bit",
        "thread_id": threading.get_ident(),
    }


def get_hardware_info(vv_instance: Any) -> Dict[str, Any]:
    """Return a dict of VibrationVIEW hardware and version info."""
    return {
        "version": vv_instance.GetSoftwareVersion(),
        "hardware_inputs": vv_instance.GetHardwareInputChannels(),
        "hardware_outputs": vv_instance.GetHardwareOutputChannels(),
        "serial_number": hex(int(vv_instance.GetHardwareSerialNumber()) & 0xFFFFFFFF),
        "is_ready": vv_instance.IsReady(),
    }


PROFILE_EXTENSIONS = {"vrp", "vrpj", "vasor", "vkp", "vkpj", "vsp", "vspj", "vdp", "vdpj", "vyp"}

DATA_EXTENSIONS = {"vrd", "vkd", "vsd", "vdd", "vyd"}  # v?d pattern

TEMPLATE_EXTENSIONS = {
    "vsyscheckt",
    "vsinet",
    "vrandomt",
    "vsort",
    "vrort",
    "vsorort",
    "vsost",
    "vanalyzert",
    "vshockt",
    "vudtt",
    "vsrst",
    "vtransientt",
}

INPUTCONFIG_EXTENSIONS = {"vic", "vchan", "inputconfig"}

REPORT_EXTENSIONS = {"vvtemplate", "rtf", "txt", "xlsx", "xlsm", "xls", "csv", "html", "htm", "pdf"}

ALLOWED_EXTENSIONS = (
    PROFILE_EXTENSIONS | DATA_EXTENSIONS | TEMPLATE_EXTENSIONS | INPUTCONFIG_EXTENSIONS | REPORT_EXTENSIONS
)


def get_folder_for_extension(filename_or_ext: str) -> str:
    """Return the appropriate folder for a given filename or extension."""
    if "." in filename_or_ext:
        ext = filename_or_ext.rsplit(".", 1)[1].lower()
    else:
        ext = filename_or_ext.lower()

    if ext in PROFILE_EXTENSIONS:
        return Config.PROFILE_FOLDER
    elif ext in DATA_EXTENSIONS:
        return Config.DATA_FOLDER
    elif ext in TEMPLATE_EXTENSIONS:
        return Config.NEW_TEST_DEFAULTS_FOLDER
    elif ext in INPUTCONFIG_EXTENSIONS:
        return Config.INPUTCONFIG_FOLDER
    elif ext in REPORT_EXTENSIONS:
        return Config.REPORT_FOLDER
    else:
        return Config.VIBRATIONVIEW_FOLDER


def handle_binary_upload(filename: str, binary_data: bytes, usetemporaryfile: bool = False) -> Dict:
    """Save uploaded binary data to disk.

    Returns:
        dict with FilePath, Filename, and Size keys.

    Raises:
        APIError: if the filename is missing, has a disallowed extension,
                  or fails sanitization.
    """
    if not filename or "." not in filename:
        raise APIError("Missing or invalid filename", "UPLOAD_ERROR")

    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise APIError(f"Invalid file extension: .{ext}", "UPLOAD_ERROR")

    base_folder = get_folder_for_extension(ext)
    temp_folder = os.path.join(base_folder, "Uploads")

    os.makedirs(temp_folder, exist_ok=True)

    if usetemporaryfile:
        unique_id = uuid.uuid4().hex
        base, base_ext = os.path.splitext(filename)
        filename = f"{base}_{unique_id}{base_ext}"

    safe_filename = secure_filename(filename)
    if not safe_filename or safe_filename.count(".") != 1:
        raise APIError("Filename is not valid after sanitization", "UPLOAD_ERROR")
    if safe_filename.rsplit(".", 1)[1].lower() != ext:
        raise APIError("File extension changed during sanitization", "UPLOAD_ERROR")
    file_path = os.path.join(temp_folder, safe_filename)

    with open(file_path, "wb") as f:
        f.write(binary_data)

    logger.info(f"Binary file saved: {file_path}")

    return {"FilePath": file_path, "Filename": filename, "Size": os.path.getsize(file_path)}


def process_file_upload(
    usetemporaryfile: bool = False,
) -> Tuple[Optional[str], Optional[str], Optional[Tuple[Dict, int]]]:
    """Detect an incoming file upload, save it, and return the result.

    Combines ``detect_file_upload`` and ``handle_binary_upload`` into a single
    call so route handlers don't need to repeat the boilerplate.

    Returns:
        (file_path, filename, error_tuple)
        - Upload saved:  (saved_file_path, original_filename, None)
        - Upload error:  (None, None, (error_dict, status_code))
        - No upload:     (None, None, None)
    """
    try:
        filename, binary_data, _content_length = detect_file_upload()
    except APIError as e:
        return None, None, (error_response(e.message, e.error_code), e.http_status)

    if filename is None:
        return None, None, None

    try:
        result = handle_binary_upload(filename, binary_data, usetemporaryfile)
    except APIError as e:
        return None, None, (error_response(e.message, e.error_code), e.http_status)

    return result["FilePath"], filename, None


def ParseVvTable(tsv_text: str) -> List[Dict[str, str]]:
    try:
        lines = tsv_text.strip().splitlines()
        if len(lines) < 2:
            return [{"RawText": tsv_text}]

        headers = lines[0].split("\t")
        data = []

        for line in lines[1:]:
            values = line.split("\t")
            if len(values) == len(headers):
                data.append(dict(zip(headers, values)))
            else:
                logger.warning(f"Skipping malformed line: {line}")

        return data

    except Exception as e:
        return [error_response(f"Error parsing TSV: {e}", "PARSE_ERROR")]


def DecodeStatusColor(status: Dict[str, int]) -> str:
    color_map = {0: "healthy", 1: "yellow", 2: "critical"}
    # Convert string to integer if needed

    return_color_code = status["stop_code_index"] >> 12
    return color_map.get(return_color_code, "unknown")


def get_channel_data(vv_instance: Any, field_keys: List[str]) -> Optional[List[Dict[str, Any]]]:
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
    field_data = {key: [vv_instance.ReportField(f"{key}{i + 1}") for i in range(channel_count)] for key in field_keys}

    # Combine into list of dictionaries per channel
    channels = []
    for i in range(channel_count):
        channel_info = {key: field_data[key][i] for key in field_keys}
        channels.append(channel_info)

    return channels


def get_last_data_file(vv_instance: Any) -> str:
    """Get the last data file path from VibrationVIEW.

    Raises APIError(400) if no file is available.
    COM exceptions propagate to @handle_errors for proper classification.
    """
    from utils.exceptions import APIError

    file_path = vv_instance.ReportField("LastDataFile")
    if not file_path:
        raise APIError(
            "No file_path provided and no last data file available in VibrationVIEW",
            "NO_DATA_FILE_AVAILABLE",
        )
    return file_path


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

    # Prepare report output directory based on output file extension
    base_folder = get_folder_for_extension(outputName)
    reportFolder = os.path.join(base_folder, "Temporary")
    os.makedirs(reportFolder, exist_ok=True)

    outPath = os.path.join(reportFolder, outputName)

    # Build and run report generation command
    command = [Config.EXE_NAME, "/savereport", filePath, "/template", templateName, "/output", outPath]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"Report generation failed.\nCommand: {' '.join(command)}\nStderr: {result.stderr.strip()}")

    return outPath


def GetVectorData(vvInstance: Any, vector: int) -> Dict[str, list]:
    try:
        cols = vvInstance.GetHardwareInputChannels() + 1
        dataList = []
        dataList.append(vvInstance.Vector(vector))

        headers = [vvInstance.VectorLabel(vector)]
        for i in range(cols - 1):
            field = f"CH{i + 1}NAME"
            headers.append(vvInstance.ReportField(field))
            dataList.append(vvInstance.Vector(vector + i))

        units = [vvInstance.VectorUnit(vector + i) for i in range(cols)]

        return {"headers": headers, "units": units, "columns": dataList}

    except Exception as e:
        raise RuntimeError(f"Error retrieving vector data: {e}")


def convert_channel_to_com_index(channel_user: Any) -> Tuple[Optional[int], Optional[Dict], Optional[int]]:
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

            return None, error_response("Channel parameter must be >= 1", "INVALID_PARAMETER"), 400
        return channel - 1, None, None
    except (ValueError, TypeError):
        from utils.response_helpers import error_response

        return None, error_response("Invalid channel parameter - must be an integer", "INVALID_PARAMETER"), 400


def is_template_file(filename: str) -> bool:
    """
    Check if a file has a template extension

    Args:
        filename: The filename to check

    Returns:
        bool: True if the file is a template file, False otherwise
    """
    if not filename or "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in TEMPLATE_EXTENSIONS


def get_new_test_defaults_path() -> str:
    """
    Get the New Test Defaults folder path from configuration

    Returns:
        str: Path to the New Test Defaults folder
    """
    return Config.NEW_TEST_DEFAULTS_FOLDER


# Pre-computed lowercase default template filenames for performance
DEFAULT_TEMPLATE_FILENAMES = {
    "random.vrandomt",
    "sine.vsinet",
    "shock.vshockt",
    "fdr.vfdrt",
    "sor.vsort",
    "sos.vsost",
    "ror.vrort",
    "sororor.vsorort",
    "srs.vsrst",
    "user-defined transient.vudtt",
    "transient.vtransientt",
    "analyzer.vanalyzert",
}


def is_default_template_filename(filename: str) -> bool:
    """
    Check if filename matches one of the default VibrationVIEW template files
    that should be copied but not opened with automation command

    Args:
        filename: The filename to check

    Returns:
        bool: True if filename matches a default template, False otherwise
    """
    return filename.lower() in DEFAULT_TEMPLATE_FILENAMES


# URN pattern: exactly 16 hexadecimal characters (e.g., "3C00000186B96114")
URN_PATTERN = re.compile(r"^[0-9A-Fa-f]{16}$")


def is_valid_urn(value: Any) -> bool:
    """
    Check if a value is a valid TEDS URN (16-digit hex string).

    Args:
        value: The value to check

    Returns:
        bool: True if value is a valid URN (16 hex digits), False otherwise

    Examples:
        is_valid_urn("3C00000186B96114")  # True
        is_valid_urn("ABC123")            # False (too short)
        is_valid_urn("No TEDS data")      # False (not hex)
    """
    if not isinstance(value, str):
        return False
    return bool(URN_PATTERN.match(value.strip()))


def detect_file_upload() -> Tuple[Optional[str], Optional[bytes], Optional[int]]:
    """
    Detect if the current request contains a file upload.

    Returns:
        tuple: (filename, binary_data, content_length) if file upload detected
        tuple: (None, None, None) if no file upload

    Raises:
        APIError: if the upload is malformed (missing filename, etc.)

    Supports:
        - multipart/form-data with any file field name
        - Raw binary body with filename in query parameter
    """
    content_type = request.content_type or ""

    logger.debug(
        f"detect_file_upload: method={request.method}, content_type={content_type}, "
        f"content_length={request.content_length}, files={list(request.files.keys())}"
    )

    # Check for multipart file upload (any field name)
    has_multipart_file = len(request.files) > 0

    # Check for raw binary upload (exclude json, form, multipart)
    is_binary_content_type = (
        request.content_length
        and request.content_length > 0
        and not has_multipart_file
        and "multipart" not in content_type
        and "application/json" not in content_type
        and "application/x-www-form-urlencoded" not in content_type
    )

    if has_multipart_file:
        # Multipart/form-data mode - get first file from any field name
        file_field = next(iter(request.files))
        uploaded_file = request.files[file_field]
        filename = uploaded_file.filename
        binary_data = uploaded_file.read()
        content_length: Optional[int] = len(binary_data)
        logger.debug(
            f"detect_file_upload: multipart file field={file_field}, filename={filename}, size={content_length}"
        )

        if not filename:
            raise APIError("Multipart file field has no filename", "UPLOAD_ERROR")

        return (filename, binary_data, content_length)

    elif is_binary_content_type:
        # Raw binary mode - get filename from query parameter
        filename = request.args.get("filename")

        if filename is None:
            query_string = request.query_string.decode("utf-8")
            if query_string:
                filename = unquote(query_string)

        if not filename:
            raise APIError(
                "Missing filename: provide via multipart/form-data file field or query parameter", "UPLOAD_ERROR"
            )

        content_length = request.content_length
        binary_data = request.get_data()
        logger.debug(f"detect_file_upload: raw binary filename={filename}, size={content_length}")

        return (filename, binary_data, content_length)

    # No file upload detected
    return (None, None, None)


def get_filename_from_request() -> Optional[str]:
    """
    Extract filename from request query parameters.

    Returns:
        str: The filename, or None if not found
    """
    filename = request.args.get("filename")

    if filename is None:
        query_string = request.query_string.decode("utf-8")
        if query_string:
            filename = unquote(query_string)

    return filename
