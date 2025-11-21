# ============================================================================
# FILE: routes/input_config.py (Input Configuration Routes)
# ============================================================================

"""
Input Configuration Routes - 1:1 VibrationVIEW COM Interface Mapping
Input channel properties, settings, and configuration operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from urllib.parse import unquote
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import convert_channel_to_com_index, handle_binary_upload, extract_com_error_info
import logging
from datetime import datetime
import config
import os

# Create blueprint
input_config_bp = Blueprint('input_config', __name__)

logger = logging.getLogger(__name__)

MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit

@input_config_bp.route('/docs/input_config', methods=['GET'])
def get_documentation():
    """Get input configuration module documentation"""
    docs = {
        'module': 'input_config',
        'description': '1:1 mapping of VibrationVIEW COM input configuration methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Input Channel Properties': {
                'GET /inputcaldate': {
                    'description': 'Get input calibration date for a channel',
                    'com_method': 'InputCalDate(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number (first query parameter)'
                    },
                    'returns': 'str - Calibration date',
                    'example': 'GET /api/inputcaldate?1'
                },
                'GET /inputserialnumber': {
                    'description': 'Get input serial number for a channel',
                    'com_method': 'InputSerialNumber(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number (first query parameter)'
                    },
                    'returns': 'str - Serial number',
                    'example': 'GET /api/inputserialnumber?1'
                },
                'GET /inputsensitivity': {
                    'description': 'Get input sensitivity for a channel',
                    'com_method': 'InputSensitivity(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number (first query parameter)'
                    },
                    'returns': 'float - Sensitivity value',
                    'example': 'GET /api/inputsensitivity?1'
                },
                'GET /inputengineeringscale': {
                    'description': 'Get input engineering scale for a channel',
                    'com_method': 'InputEngineeringScale(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number (first query parameter)'
                    },
                    'returns': 'float - Engineering scale value',
                    'example': 'GET /api/inputengineeringscale?1'
                }
            },
            'Input Channel Settings (Get/Set)': {
                'GET|POST /inputcapacitorcoupled': {
                    'description': 'Get/Set input capacitor coupled setting',
                    'com_method': 'InputCapacitorCoupled(channel) or InputCapacitorCoupled(channel, value)',
                    'parameters': {
                        'channel': 'int - Input channel number',
                        'value': 'bool - Coupling setting (POST only)'
                    },
                    'returns': 'bool - Current coupling setting'
                },
                'GET|POST /inputaccelpowersource': {
                    'description': 'Get/Set input accelerometer power source',
                    'com_method': 'InputAccelPowerSource(channel) or InputAccelPowerSource(channel, value)',
                    'parameters': {
                        'channel': 'int - Input channel number',
                        'value': 'bool - Power source setting (POST only)'
                    },
                    'returns': 'bool - Current power source setting'
                },
                'GET|POST /inputdifferential': {
                    'description': 'Get/Set input differential setting',
                    'com_method': 'InputDifferential(channel) or InputDifferential(channel, value)',
                    'parameters': {
                        'channel': 'int - Input channel number',
                        'value': 'bool - Differential setting (POST only)'
                    },
                    'returns': 'bool - Current differential setting'
                }
            },
            'Input Configuration': {
                'POST /inputmode': {
                    'description': 'Set input mode for a channel',
                    'com_method': 'InputMode(channel, powerSource, capCoupled, differential)',
                    'parameters': {
                        'channel': 'int - Input channel number',
                        'powersource': 'bool - Power source setting',
                        'capcoupled': 'bool - Capacitor coupled setting',
                        'differential': 'bool - Differential setting'
                    },
                    'returns': 'bool - Success status'
                },
                'POST /inputcalibration': {
                    'description': 'Set input calibration for a channel',
                    'com_method': 'InputCalibration(channel, sensitivity, serialNumber, calDate)',
                    'parameters': {
                        'channel': 'int - Input channel number',
                        'sensitivity': 'float - Sensitivity value',
                        'serialnumber': 'str - Serial number',
                        'caldate': 'str - Calibration date'
                    },
                    'returns': 'bool - Success status'
                },
                'GET|POST /setinputconfigurationfile': {
                    'description': 'Get/Set input configuration file',
                    'com_method': 'GetInputConfigurationFile() or SetInputConfigurationFile(configName)',
                    'parameters': {
                        'configName': 'str - Configuration file name (POST URL parameter only)'
                    },
                    'returns': 'str|bool - Current config name (GET) or success status (POST)',
                    'example': 'POST /api/setinputconfigurationfile?configName=10mv per G.vic or ' +
                               '/api/setinputconfigurationfile?10mv per G.vic'
                },
                'PUT /openinputconfigurationfile': {
                    'description': 'Upload and load input configuration file',
                    'com_method': 'SetInputConfigurationFile(filepath)',
                    'parameters': {
                        'filename': 'str - Configuration file name (URL parameter)',
                        'binary_data': 'bytes - File content in request body'
                    },
                    'headers': {
                        'Content-Length': 'Required - File size in bytes (max 10MB)'
                    },
                    'returns': 'dict - Success status and file info',
                    'example': 'PUT /api/openinputconfigurationfile?10mv per G.vic (with binary file in body)'
                }
            }
        },
        'notes': [
            'GET requests return current parameter value for get/set endpoints',
            'POST requests with JSON body parameters perform operations',
            'Channel numbers are 0-based (first channel is 0)',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

# Input Channel Properties
@input_config_bp.route('/inputcaldate', methods=['GET'])
@handle_errors
@with_vibrationview
def input_cal_date(vv_instance):
    """
    Get Input Calibration Date
    
    COM Method: InputCalDate(channel)
    Returns the calibration date for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
    
    Example: GET /api/inputcaldate?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    result = vv_instance.InputCalDate(channel_com)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel_user},
        f"Channel {channel_user} calibration date: {result}"
    ))

@input_config_bp.route('/inputserialnumber', methods=['GET'])
@handle_errors
@with_vibrationview
def input_serial_number(vv_instance):
    """
    Get Input Serial Number
    
    COM Method: InputSerialNumber(channel)
    Returns the serial number for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
    
    Example: GET /api/inputserialnumber?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    result = vv_instance.InputSerialNumber(channel_com)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel_user},
        f"Channel {channel_user} serial number: {result}"
    ))

@input_config_bp.route('/inputsensitivity', methods=['GET'])
@handle_errors
@with_vibrationview
def input_sensitivity(vv_instance):
    """
    Get Input Sensitivity
    
    COM Method: InputSensitivity(channel)
    Returns the sensitivity value for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
    
    Example: GET /api/inputsensitivity?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    result = vv_instance.InputSensitivity(channel_com)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel_user},
        f"Channel {channel_user} sensitivity: {result}"
    ))

@input_config_bp.route('/inputengineeringscale', methods=['GET'])
@handle_errors
@with_vibrationview
def input_engineering_scale(vv_instance):
    """
    Get Input Engineering Scale
    
    COM Method: InputEngineeringScale(channel)
    Returns the engineering scale for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
    
    Example: GET /api/inputengineeringscale?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    result = vv_instance.InputEngineeringScale(channel_com)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel_user},
        f"Channel {channel_user} engineering scale: {result}"
    ))

# Input Channel Settings (Get/Set)
@input_config_bp.route('/inputcapacitorcoupled', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_capacitor_coupled(vv_instance):
    """
    Get/Set Input Capacitor Coupled
    
    COM Method: InputCapacitorCoupled(channel) or InputCapacitorCoupled(channel, value)
    Gets or sets the capacitor coupled setting for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
        Example: GET /api/inputcapacitorcoupled?1
    
    POST Query Parameters for setting:
        channel: Input channel number (1-based) - first positional parameter
        value: Coupling setting (true/false) - second positional parameter
        Example: POST /api/inputcapacitorcoupled?1&true
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputCapacitorCoupled(channel_com)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user},
            f"Channel {channel_user} capacitor coupled: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputCapacitorCoupled(channel_com, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user, 'value_set': value},
            f"Channel {channel_user} capacitor coupled set to {value}, returned: {result}"
        ))

@input_config_bp.route('/inputaccelpowersource', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_accel_power_source(vv_instance):
    """
    Get/Set Input Accelerometer Power Source
    
    COM Method: InputAccelPowerSource(channel) or InputAccelPowerSource(channel, value)
    Gets or sets the accelerometer power source for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
        Example: GET /api/inputaccelpowersource?1
    
    POST Query Parameters for setting:
        channel: Input channel number (1-based) - first positional parameter
        value: Power source setting (true/false) - second positional parameter
        Example: POST /api/inputaccelpowersource?1&true
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputAccelPowerSource(channel_com)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user},
            f"Channel {channel_user} accel power source: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputAccelPowerSource(channel_com, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user, 'value_set': value},
            f"Channel {channel_user} accel power source set to {value}, returned: {result}"
        ))

@input_config_bp.route('/inputdifferential', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_differential(vv_instance):
    """
    Get/Set Input Differential
    
    COM Method: InputDifferential(channel) or InputDifferential(channel, value)
    Gets or sets the differential setting for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
        Example: GET /api/inputdifferential?1
    
    POST Query Parameters for setting:
        channel: Input channel number (1-based) - first positional parameter
        value: Differential setting (true/false) - second positional parameter
        Example: POST /api/inputdifferential?1&true
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(query_args[0])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(query_args[0])  # Keep original for response
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputDifferential(channel_com)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user},
            f"Channel {channel_user} differential: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputDifferential(channel_com, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel_user, 'value_set': value},
            f"Channel {channel_user} differential set to {value}, returned: {result}"
        ))

# Input Configuration
@input_config_bp.route('/inputmode', methods=['POST'])
@handle_errors
@with_vibrationview
def input_mode(vv_instance):
    """
    Set Input Mode
    
    COM Method: InputMode(channel, powerSource, capCoupled, differential)
    Sets the input mode configuration for the specified channel.
    
    JSON Parameters:
        channel: Input channel number (1-based)
        powersource: Power source setting
        capcoupled: Capacitor coupled setting
        differential: Differential setting
    """
    data = request.get_json()
    required_params = ['channel', 'powersource', 'capcoupled', 'differential']

    if not data:
        return jsonify(error_response(
            'Missing JSON body',
            'MISSING_BODY'
        )), 400
    
    missing_params = [param for param in required_params if param not in data]
    if missing_params:
        return jsonify(error_response(
            f'Missing required parameters: {", ".join(missing_params)}',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(data['channel'])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(data['channel'])  # Keep original for response
    
    vv_instance.InputMode(
        channel_com,
        data['powersource'],
        data['capcoupled'],
        data['differential']
    )
    
    result = True
    return jsonify(success_response(
        {
            'result': result,
            'channel': channel_user,
            'powersource': data['powersource'],
            'capcoupled': data['capcoupled'],
            'differential': data['differential']
        },
        f"Channel {channel_user} input mode {'configured successfully' if result else 'configuration failed'}"
    ))

@input_config_bp.route('/inputcalibration', methods=['POST'])
@handle_errors
@with_vibrationview
def input_calibration(vv_instance):
    """
    Set Input Calibration
    
    COM Method: InputCalibration(channel, sensitivity, serialNumber, calDate)
    Sets the calibration information for the specified input channel.
    
    JSON Parameters:
        channel: Input channel number (1-based)
        sensitivity: Sensitivity value
        serialnumber: Serial number
        caldate: Calibration date
    """
    data = request.get_json()
    required_params = ['channel', 'sensitivity', 'serialnumber', 'caldate']

    if not data:
        return jsonify(error_response(
            'Missing JSON body',
            'MISSING_BODY'
        )), 400
    
    missing_params = [param for param in required_params if param not in data]
    if missing_params:
        return jsonify(error_response(
            f'Missing required parameters: {", ".join(missing_params)}',
            'MISSING_PARAMETER'
        )), 400
    
    channel_com, error_resp, status_code = convert_channel_to_com_index(data['channel'])
    if error_resp:
        return jsonify(error_resp), status_code
    
    channel_user = int(data['channel'])  # Keep original for response
    
    result = True # If no exception, assume success
    vv_instance.InputCalibration(
        channel_com,
        data['sensitivity'],
        data['serialnumber'],
        data['caldate']
    )
    
    return jsonify(success_response(
        {
            'result': result,
            'channel': channel_user,
            'sensitivity': data['sensitivity'],
            'serialnumber': data['serialnumber'],
            'caldate': data['caldate']
        },
        f"Channel {channel_user} calibration {'set successfully' if result else 'setting failed'}"
    ))

@input_config_bp.route('/setinputconfigurationfile', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def set_input_configuration_file(vv_instance):
    """
    Get/Set Input Configuration File
    
    COM Method: GetInputConfigurationFile() or SetInputConfigurationFile(configName)
    Gets current configuration file or loads a new input configuration file.
    GET: Returns current configuration file name
    POST: Sets configuration file from URL parameter 'configName' or unnamed parameter
    
    Example: POST /api/setinputconfigurationfile?configName=10mv per G.vic or 
             POST /api/setinputconfigurationfile?10mv per G.vic
    """
    if request.method == "GET" and not request.args:
        # GET without parameters - return current configuration file
        result = vv_instance.GetInputConfigurationFile()
        return jsonify(
            success_response(
                {"result": result}, f"Current input configuration file: {result}"
            )
        )
    else:
        # Set configuration file from parameters
        config_name = request.args.get("configName")
        
        # If no 'configName' parameter, try to get the first unnamed parameter
        if config_name is None:
            args = list(request.args.keys())
            if args:
                config_name = args[0]
        
        if config_name is None:
            return (
                jsonify(
                    error_response(
                        "Missing required URL parameter: configName (or unnamed parameter)",
                        "MISSING_PARAMETER"
                    )
                ),
                400,
            )

        vv_instance.SetInputConfigurationFile(config_name)
        return jsonify(
            success_response(
                {"configName": config_name},
                f"Input configuration file '{config_name}' loaded successfully"
            )
        )


@input_config_bp.route('/openinputconfigurationfile', methods=['PUT'])
@with_vibrationview
def upload_and_open_input_configuration_file(vv_instance):
    """
    Upload and Open Input Configuration File
    
    COM Method: SetInputConfigurationFile(filepath)
    Uploads an input configuration file (.vic) and loads it.
    
    Query Parameters:
        filename: string - Configuration filename (named parameter)
        OR unnamed parameter: string - Configuration filename as first URL parameter
    
    Headers:
        Content-Length: Required - File size in bytes (max 10MB)
    
    Body:
        Binary file content
    
    Example: PUT /api/openinputconfigurationfile?filename=10mv per G.vic or 
             PUT /api/openinputconfigurationfile?10mv per G.vic (with binary file in body)
    """
    try:
        # Get filename from parameters - check named parameter first, then unnamed
        filename = request.args.get("filename")
        
        # If no 'filename' parameter, try to get the first unnamed parameter
        if filename is None:
            query_string = request.query_string.decode('utf-8')
            if query_string:
                # URL decode the query string to handle special characters
                filename = unquote(query_string)
        
        content_length = request.content_length

        if not filename:
            return jsonify({'Error': 'Missing required query parameter: filename (or unnamed filename parameter)'}), 400

        if content_length is None:
            return jsonify({'Error': 'Missing Content-Length header'}), 411  # Length Required
        
        if content_length > MAX_CONTENT_LENGTH:
            return jsonify({'Error': 'File too large (max 10MB)'}), 413  # Payload Too Large
        
        binary_data = request.get_data()
        
        # Handle file upload - build absolute path using config folder + uploads subfolder
        uploads_folder = os.path.join(config.Config.INPUTCONFIG_FOLDER, 'Uploads')
        result, error, status_code = handle_binary_upload(filename, binary_data, uploadsubfolder=uploads_folder)
        
        if error:
            return jsonify(error), status_code

        file_path = result['FilePath']

        # Load the uploaded configuration file
        vv_instance.SetInputConfigurationFile(file_path)

        # Handle void return - assume success if no exception was raised
        success = True
        
        return jsonify(success_response(
            {
                'result': success,
                'filepath': filename,
                'executed': True
            },
            f"SetInputConfigurationFile command {'executed successfully' if success else 'failed'}: {filename}"
        ))

    except Exception as e:
        return jsonify(extract_com_error_info(e)), 500
