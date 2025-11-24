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
            'COM interface uses 0-based indexing for all arrays',
            'Input-specific endpoints moved to input_config module: /api/v1/docs/input_config'
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
    
    Example: GET /api/v1/hardwaresupportscapacitorcoupled?1
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
    
    Example: GET /api/v1/hardwaresupportsaccelpowersource?1
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
    
    Example: GET /api/v1/hardwaresupportsdifferential?1
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