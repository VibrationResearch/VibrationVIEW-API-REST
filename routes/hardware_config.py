# ============================================================================
# FILE: routes/hardware_config.py (Hardware Configuration Routes) - v34
# ============================================================================

"""
Hardware Configuration Routes - 1:1 VibrationVIEW COM Interface Mapping
Hardware and input configuration operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging
from datetime import datetime

# Create blueprint
hardware_config_bp = Blueprint('hardware_config', __name__)

logger = logging.getLogger(__name__)

@hardware_config_bp.route('/docs/hardware_config', methods=['GET'])
def get_documentation():
    """Get hardware configuration module documentation"""
    docs = {
        'module': 'hardware_config',
        'description': '1:1 mapping of VibrationVIEW COM hardware configuration methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Hardware Information': {
                'GET /gethardwareinputchannels': {
                    'description': 'Get number of hardware input channels',
                    'com_method': 'GetHardwareInputChannels()',
                    'parameters': 'None',
                    'returns': 'int - Number of input channels'
                },
                'GET /gethardwareoutputchannels': {
                    'description': 'Get number of hardware output channels',
                    'com_method': 'GetHardwareOutputChannels()',
                    'parameters': 'None',
                    'returns': 'int - Number of output channels'
                },
                'GET /gethardwareserialnumber': {
                    'description': 'Get hardware serial number',
                    'com_method': 'GetHardwareSerialNumber()',
                    'parameters': 'None',
                    'returns': 'str - Hardware serial number'
                },
                'GET /getsoftwareversion': {
                    'description': 'Get software version',
                    'com_method': 'GetSoftwareVersion()',
                    'parameters': 'None',
                    'returns': 'str - Software version'
                }
            },
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
                        'powerSource': 'bool - Power source setting',
                        'capCoupled': 'bool - Capacitor coupled setting',
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
                        'serialNumber': 'str - Serial number',
                        'calDate': 'str - Calibration date'
                    },
                    'returns': 'bool - Success status'
                },
                'POST /setinputconfigurationfile': {
                    'description': 'Load input configuration file',
                    'com_method': 'SetInputConfigurationFile(configName)',
                    'parameters': {
                        'configName': 'str - Configuration file name'
                    },
                    'returns': 'bool - Success status'
                }
            },
            'Hardware Capability Checks': {
                'POST /hardwaresupportscapacitorcoupled': {
                    'description': 'Check if hardware supports capacitor coupled',
                    'com_method': 'HardwareSupportsCapacitorCoupled(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number'
                    },
                    'returns': 'bool - Support status'
                },
                'POST /hardwaresupportsaccelpowersource': {
                    'description': 'Check if hardware supports accelerometer power source',
                    'com_method': 'HardwareSupportsAccelPowerSource(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number'
                    },
                    'returns': 'bool - Support status'
                },
                'POST /hardwaresupportsdifferential': {
                    'description': 'Check if hardware supports differential',
                    'com_method': 'HardwareSupportsDifferential(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number'
                    },
                    'returns': 'bool - Support status'
                }
            }
        },
        'notes': [
            'GET requests return current parameter value for get/set endpoints',
            'POST requests with JSON body parameters perform operations',
            'Channel numbers are 0-based (first channel is 0)',
            'Hardware capability checks help determine available features',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

# Hardware Information
@hardware_config_bp.route('/gethardwareinputchannels', methods=['GET'])
@handle_errors
@with_vibrationview
def get_hardware_input_channels(vv_instance):
    """
    Get Hardware Input Channels
    
    COM Method: GetHardwareInputChannels()
    Returns the number of input channels available on the hardware.
    """
    result = vv_instance.GetHardwareInputChannels()
    
    return jsonify(success_response(
        {'result': result},
        f"Hardware input channels: {result}"
    ))

@hardware_config_bp.route('/gethardwareoutputchannels', methods=['GET'])
@handle_errors
@with_vibrationview
def get_hardware_output_channels(vv_instance):
    """
    Get Hardware Output Channels
    
    COM Method: GetHardwareOutputChannels()
    Returns the number of output channels available on the hardware.
    """
    result = vv_instance.GetHardwareOutputChannels()
    
    return jsonify(success_response(
        {'result': result},
        f"Hardware output channels: {result}"
    ))

@hardware_config_bp.route('/gethardwareserialnumber', methods=['GET'])
@handle_errors
@with_vibrationview
def get_hardware_serial_number(vv_instance):
    """
    Get Hardware Serial Number
    
    COM Method: GetHardwareSerialNumber()
    Returns the serial number of the connected hardware.
    """
    result = vv_instance.GetHardwareSerialNumber()
    
    return jsonify(success_response(
        {'result': result},
        f"Hardware serial number: {result}"
    ))

@hardware_config_bp.route('/getsoftwareversion', methods=['GET'])
@handle_errors
@with_vibrationview
def get_software_version(vv_instance):
    """
    Get Software Version
    
    COM Method: GetSoftwareVersion()
    Returns the version of the VibrationVIEW software.
    """
    result = vv_instance.GetSoftwareVersion()
    
    return jsonify(success_response(
        {'result': result},
        f"Software version: {result}"
    ))

# Input Channel Properties
@hardware_config_bp.route('/inputcaldate', methods=['GET'])
@handle_errors
@with_vibrationview
def input_cal_date(vv_instance):
    """
    Get Input Calibration Date
    
    COM Method: InputCalDate(channel)
    Returns the calibration date for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/inputcaldate?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.InputCalDate(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} calibration date: {result}"
    ))

@hardware_config_bp.route('/inputserialnumber', methods=['GET'])
@handle_errors
@with_vibrationview
def input_serial_number(vv_instance):
    """
    Get Input Serial Number
    
    COM Method: InputSerialNumber(channel)
    Returns the serial number for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/inputserialnumber?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.InputSerialNumber(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} serial number: {result}"
    ))

@hardware_config_bp.route('/inputsensitivity', methods=['GET'])
@handle_errors
@with_vibrationview
def input_sensitivity(vv_instance):
    """
    Get Input Sensitivity
    
    COM Method: InputSensitivity(channel)
    Returns the sensitivity value for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/inputsensitivity?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.InputSensitivity(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} sensitivity: {result}"
    ))

@hardware_config_bp.route('/inputengineeringscale', methods=['GET'])
@handle_errors
@with_vibrationview
def input_engineering_scale(vv_instance):
    """
    Get Input Engineering Scale
    
    COM Method: InputEngineeringScale(channel)
    Returns the engineering scale for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/inputengineeringscale?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.InputEngineeringScale(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} engineering scale: {result}"
    ))

# Input Channel Settings (Get/Set)
@hardware_config_bp.route('/inputcapacitorcoupled', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_capacitor_coupled(vv_instance):
    """
    Get/Set Input Capacitor Coupled
    
    COM Method: InputCapacitorCoupled(channel) or InputCapacitorCoupled(channel, value)
    Gets or sets the capacitor coupled setting for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
        Example: GET /api/inputcapacitorcoupled?1
    
    POST Query Parameters for setting:
        channel: Input channel number (0-based) - first positional parameter
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
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputCapacitorCoupled(channel)
        return jsonify(success_response(
            {'result': result, 'channel': channel},
            f"Channel {channel} capacitor coupled: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputCapacitorCoupled(channel, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel, 'value_set': value},
            f"Channel {channel} capacitor coupled set to {value}, returned: {result}"
        ))

@hardware_config_bp.route('/inputaccelpowersource', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_accel_power_source(vv_instance):
    """
    Get/Set Input Accelerometer Power Source
    
    COM Method: InputAccelPowerSource(channel) or InputAccelPowerSource(channel, value)
    Gets or sets the accelerometer power source for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
        Example: GET /api/inputaccelpowersource?1
    
    POST Query Parameters for setting:
        channel: Input channel number (0-based) - first positional parameter
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
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputAccelPowerSource(channel)
        return jsonify(success_response(
            {'result': result, 'channel': channel},
            f"Channel {channel} accel power source: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputAccelPowerSource(channel, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel, 'value_set': value},
            f"Channel {channel} accel power source set to {value}, returned: {result}"
        ))

@hardware_config_bp.route('/inputdifferential', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def input_differential(vv_instance):
    """
    Get/Set Input Differential
    
    COM Method: InputDifferential(channel) or InputDifferential(channel, value)
    Gets or sets the differential setting for the specified input channel.
    
    GET Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
        Example: GET /api/inputdifferential?1
    
    POST Query Parameters for setting:
        channel: Input channel number (0-based) - first positional parameter
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
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    if request.method == 'GET' or len(query_args) < 2:
        result = vv_instance.InputDifferential(channel)
        return jsonify(success_response(
            {'result': result, 'channel': channel},
            f"Channel {channel} differential: {result}"
        ))
    else:
        try:
            value = query_args[1].lower() == 'true'
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid value parameter - must be true or false',
                'INVALID_PARAMETER'
            )), 400
        
        result = vv_instance.InputDifferential(channel, value)
        return jsonify(success_response(
            {'result': result, 'channel': channel, 'value_set': value},
            f"Channel {channel} differential set to {value}, returned: {result}"
        ))

# Input Configuration
@hardware_config_bp.route('/inputmode', methods=['POST'])
@handle_errors
@with_vibrationview
def input_mode(vv_instance):
    """
    Set Input Mode
    
    COM Method: InputMode(channel, powerSource, capCoupled, differential)
    Sets the input mode configuration for the specified channel.
    
    JSON Parameters:
        channel: Input channel number (0-based)
        powerSource: Power source setting
        capCoupled: Capacitor coupled setting
        differential: Differential setting
    """
    data = request.get_json()
    required_params = ['channel', 'powerSource', 'capCoupled', 'differential']
    
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
    
    vv_instance.InputMode(
        data['channel'],
        data['powerSource'],
        data['capCoupled'],
        data['differential']
    )
    
    result = True
    return jsonify(success_response(
        {
            'result': result,
            'channel': data['channel'],
            'powerSource': data['powerSource'],
            'capCoupled': data['capCoupled'],
            'differential': data['differential']
        },
        f"Channel {data['channel']} input mode {'configured successfully' if result else 'configuration failed'}"
    ))

@hardware_config_bp.route('/inputcalibration', methods=['POST'])
@handle_errors
@with_vibrationview
def input_calibration(vv_instance):
    """
    Set Input Calibration
    
    COM Method: InputCalibration(channel, sensitivity, serialNumber, calDate)
    Sets the calibration information for the specified input channel.
    
    JSON Parameters:
        channel: Input channel number (0-based)
        sensitivity: Sensitivity value
        serialNumber: Serial number
        calDate: Calibration date
    """
    data = request.get_json()
    required_params = ['channel', 'sensitivity', 'serialNumber', 'calDate']
    
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
    
    result = vv_instance.InputCalibration(
        data['channel'],
        data['sensitivity'],
        data['serialNumber'],
        data['calDate']
    )
    
    return jsonify(success_response(
        {
            'result': result,
            'channel': data['channel'],
            'sensitivity': data['sensitivity'],
            'serialNumber': data['serialNumber'],
            'calDate': data['calDate']
        },
        f"Channel {data['channel']} calibration {'set successfully' if result else 'setting failed'}"
    ))

@hardware_config_bp.route('/setinputconfigurationfile', methods=['POST'])
@handle_errors
@with_vibrationview
def set_input_configuration_file(vv_instance):
    """
    Set Input Configuration File
    
    COM Method: SetInputConfigurationFile(configName)
    Loads an input configuration file.
    
    JSON Parameters:
        configName: Configuration file name
    """
    data = request.get_json()
    if not data or 'configName' not in data:
        return jsonify(error_response(
            'Missing required parameter: configName',
            'MISSING_PARAMETER'
        )), 400
    
    result = vv_instance.SetInputConfigurationFile(data['configName'])
    
    return jsonify(success_response(
        {'result': result, 'configName': data['configName']},
        f"Input configuration file '{data['configName']}' {'loaded successfully' if result else 'loading failed'}"
    ))

# Hardware Capability Checks
@hardware_config_bp.route('/hardwaresupportscapacitorcoupled', methods=['GET'])
@handle_errors
@with_vibrationview
def hardware_supports_capacitor_coupled(vv_instance):
    """
    Hardware Supports Capacitor Coupled
    
    COM Method: HardwareSupportsCapacitorCoupled(channel)
    Checks if the hardware supports capacitor coupled for the specified channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/hardwaresupportscapacitorcoupled?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.HardwareSupportsCapacitorCoupled(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} capacitor coupled support: {result}"
    ))

@hardware_config_bp.route('/hardwaresupportsaccelpowersource', methods=['GET'])
@handle_errors
@with_vibrationview
def hardware_supports_accel_power_source(vv_instance):
    """
    Hardware Supports Accelerometer Power Source
    
    COM Method: HardwareSupportsAccelPowerSource(channel)
    Checks if the hardware supports accelerometer power source for the specified channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/hardwaresupportsaccelpowersource?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.HardwareSupportsAccelPowerSource(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} accel power source support: {result}"
    ))

@hardware_config_bp.route('/hardwaresupportsdifferential', methods=['GET'])
@handle_errors
@with_vibrationview
def hardware_supports_differential(vv_instance):
    """
    Hardware Supports Differential
    
    COM Method: HardwareSupportsDifferential(channel)
    Checks if the hardware supports differential for the specified channel.
    
    Query Parameters:
        channel: Input channel number (0-based) - first positional parameter
    
    Example: GET /api/hardwaresupportsdifferential?1
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    result = vv_instance.HardwareSupportsDifferential(channel)
    
    return jsonify(success_response(
        {'result': result, 'channel': channel},
        f"Channel {channel} differential support: {result}"
    ))