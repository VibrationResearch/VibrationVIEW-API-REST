# ============================================================================
# FILE: routes/teds.py (TEDS Information Routes) - v34
# ============================================================================

"""
TEDS Information Routes - 1:1 VibrationVIEW COM Interface Mapping
TEDS (Transducer Electronic Data Sheet) operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.teds_formatter import format_teds_data, format_single_channel_teds
import logging
from datetime import datetime

# Create blueprint
teds_bp = Blueprint('teds', __name__)

logger = logging.getLogger(__name__)

@teds_bp.route('/docs/teds', methods=['GET'])
def get_documentation():
    """Get TEDS module documentation"""
    docs = {
        'module': 'teds',
        'description': '1:1 mapping of VibrationVIEW COM TEDS information methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'TEDS Information': {
                'GET /inputteds': {
                    'description': 'Get TEDS information for all input channels',
                    'com_method': 'Teds(channel) for each channel',
                    'parameters': 'None',
                    'returns': 'array - TEDS information for all channels'
                },
                'GET /inputtedschannel': {
                    'description': 'Get TEDS information for a specific channel',
                    'com_method': 'Teds(channel)',
                    'parameters': {
                        'channel': 'int - Input channel number (1-based, first query parameter)'
                    },
                    'returns': 'object - TEDS information for specified channel',
                    'example': 'GET /api/v1/inputtedschannel?3 (channel 3, 1-based)'
                },
                'GET /teds': {
                    'description': 'Get formatted TEDS information for specific channel or all channels',
                    'com_method': 'Teds(channel) or Teds()',
                    'parameters': {
                        'channel': 'int - Optional channel number (1-based, first query parameter)'
                    },
                    'returns': 'object - Structured transducer data for specific channel or transducers/errors arrays for all channels',
                    'examples': [
                        'GET /api/v1/teds (all channels - transducers/errors arrays)',
                        'GET /api/v1/teds?3 (channel 3, 1-based - single transducer object)'
                    ]
                },
                'GET|POST /tedsreadandapply': {
                    'description': 'Read and apply TEDS information for all channels',
                    'com_method': 'TedsReadAndApply()',
                    'parameters': 'None',
                    'returns': 'object - Success status and operation result',
                    'example': 'GET /api/v1/tedsreadandapply or POST /api/v1/tedsreadandapply'
                },
                'POST /tedsverifyandapply': {
                    'description': 'Verify and apply TEDS information for specified URNs',
                    'com_method': 'TedsVerifyAndApply(urns)',
                    'parameters': {
                        'urns': 'array - List of URN strings to verify and apply TEDS for'
                    },
                    'returns': 'object - Success status and operation result',
                    'example': 'POST /api/v1/tedsverifyandapply with JSON body: {"urns": ["urn1", "urn2"]}'
                },
                'GET|POST /tedsread': {
                    'description': 'Read TEDS information from hardware',
                    'com_method': 'TedsRead()',
                    'parameters': 'None',
                    'returns': 'object - Success status and operation result',
                    'example': 'GET /api/v1/tedsread or POST /api/v1/tedsread'
                },
                'GET /tedsfromurn': {
                    'description': 'Lookup formatted TEDS transducer by Unique Registration Number (URN)',
                    'com_method': 'TedsFromURN(urn)',
                    'parameters': {
                        'urn': 'string - Unique Registration Number (first query parameter)'
                    },
                    'returns': 'object - Formatted transducer data for the specified URN',
                    'example': 'GET /api/v1/tedsfromurn?urn123456'
                }
            }
        },
        'notes': [
            'TEDS (Transducer Electronic Data Sheet) contains sensor information',
            'All routes now use 1-based channel indexing for consistency (user-friendly)',
            'Channels are automatically converted to 0-based for VibrationVIEW COM interface',
            'Channels without TEDS data will return error information',
            'COM interface uses 0-based indexing internally but this is handled automatically'
        ]
    }
    return jsonify(docs)

@teds_bp.route('/inputteds', methods=['GET'])
@handle_errors
@with_vibrationview
def get_input_teds_all(vv_instance):
    """
    Get TEDS Information for All Channels
    
    COM Method: Teds(channel) for each available channel
    Returns TEDS information for all input channels on the hardware.
    Channels without TEDS will include error information.
    """
    all_teds_data = []
    num_channels = vv_instance.GetHardwareInputChannels()
    
    for channel in range(num_channels):
        try:
            teds_info = vv_instance.Teds(channel)
            teds_data = {
                "channel": channel + 1,  # 1-based for display
                "success": True,
                "teds": teds_info
            }
            all_teds_data.append(teds_data)

        except Exception as e:
            teds_error = {
                "channel": channel + 1,  # 1-based for display
                "success": False,
                "error": str(e),
                "teds": []
            }
            all_teds_data.append(teds_error)

    # Count channels with actual TEDS data and errors
    channels_with_teds_data = 0
    channels_with_errors = 0
    
    for t in all_teds_data:
        if not t.get('success', True):
            # Channel failed to retrieve TEDS data
            channels_with_errors += 1
        elif 'teds' in t:
            # Check if TEDS data contains actual information
            teds_data = t['teds']
            has_real_teds = False
            has_error = False
            
            if isinstance(teds_data, list):
                if len(teds_data) == 0:
                    # Empty list - no TEDS data
                    pass
                else:
                    for teds_entry in teds_data:
                        if isinstance(teds_entry, dict):
                            if "Error" in teds_entry:
                                has_error = True
                                break
                            elif "Teds" in teds_entry:
                                # VibrationVIEW format with "Teds" array
                                if isinstance(teds_entry["Teds"], list) and len(teds_entry["Teds"]) > 0:
                                    has_real_teds = True
                                    break
                            elif len(teds_entry) > 0:
                                # Direct TEDS data (like mock format with sensitivity, units, etc.)
                                has_real_teds = True
                                break
            elif isinstance(teds_data, dict) and len(teds_data) > 0:
                # Direct dict format (mock or simplified format)
                if "Error" not in teds_data:
                    has_real_teds = True
            
            if has_error:
                channels_with_errors += 1
            elif has_real_teds:
                channels_with_teds_data += 1

    # Calculate total channels with TEDS enabled (data + errors)
    channels_with_teds_enabled = channels_with_teds_data + channels_with_errors

    return jsonify(success_response(
        {
            'result': all_teds_data,
            'total_channels': num_channels,
            'channels_with_teds': channels_with_teds_data,
            'channels_with_errors': channels_with_errors,
            'channels_with_teds_enabled': channels_with_teds_enabled
        },
        f"TEDS information retrieved for {num_channels} channels"
    ))

@teds_bp.route('/inputtedschannel', methods=['GET'])
@handle_errors
@with_vibrationview
def get_input_teds_channel(vv_instance):
    """
    Get TEDS Information for Specific Channel (1-based indexing)
    
    COM Method: Teds(channel)
    Returns TEDS information for the specified input channel.
    
    Query Parameters:
        channel: Input channel number (1-based) - first positional parameter
    
    Example: GET /api/v1/inputtedschannel?3 (gets channel 3, 1-based)
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: channel',
            'MISSING_PARAMETER'
        )), 400
    
    try:
        channel_1based = int(query_args[0])
    except (ValueError, IndexError):
        return jsonify(error_response(
            'Invalid channel parameter - must be an integer',
            'INVALID_PARAMETER'
        )), 400
    
    # Validate 1-based channel number
    if channel_1based < 1:
        return jsonify(error_response(
            f'Channel must be >= 1 (1-based indexing), got {channel_1based}',
            'INVALID_CHANNEL'
        )), 400
    
    # Convert from 1-based to 0-based for COM interface
    channel_0based = channel_1based - 1
    
    # Validate channel range
    num_channels = vv_instance.GetHardwareInputChannels()
    if channel_0based >= num_channels:
        return jsonify(error_response(
            f'Channel {channel_1based} out of range - must be 1 to {num_channels} (1-based)',
            'CHANNEL_OUT_OF_RANGE'
        )), 400
    
    try:
        teds_info = vv_instance.Teds(channel_0based)
        
        return jsonify(success_response(
            {
                'result': teds_info,
                'channel': channel_1based,
                'internal_channel': channel_0based,
                'success': True
            },
            f"TEDS information retrieved for channel {channel_1based} (1-based)"
        ))
        
    except Exception as e:
        return jsonify(error_response(
            f'Failed to retrieve TEDS for channel {channel_1based}: {str(e)}',
            'TEDS_READ_ERROR'
        )), 500

@teds_bp.route('/teds', methods=['GET'])
@handle_errors
@with_vibrationview
def teds(vv_instance):
    """
    Get TEDS Information for Specific Channel or All Channels (1-based indexing)
    
    COM Method: Teds(channel) or Teds()
    Returns TEDS information for the specified channel (1-based) or all channels if no channel specified.
    
    Query Parameters:
        channel: Optional input channel number (1-based) - first positional parameter
    
    Examples: 
        GET /api/v1/teds (all channels)
        GET /api/v1/teds?3 (channel 3, 1-based)
    """
    # Get channel from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    
    if query_args:
        # Channel specified - get specific channel TEDS (1-based)
        try:
            channel_1based = int(query_args[0])
        except (ValueError, IndexError):
            return jsonify(error_response(
                'Invalid channel parameter - must be an integer',
                'INVALID_PARAMETER'
            )), 400
        
        # Validate 1-based channel number
        if channel_1based < 1:
            return jsonify(error_response(
                f'Channel must be >= 1 (1-based indexing), got {channel_1based}',
                'INVALID_CHANNEL'
            )), 400
        
        # Convert from 1-based to 0-based
        channel_0based = channel_1based - 1
        
        # Validate channel range
        num_channels = vv_instance.GetHardwareInputChannels()
        if channel_0based >= num_channels:
            return jsonify(error_response(
                f'Channel {channel_1based} out of range - must be 1 to {num_channels} (1-based)',
                'CHANNEL_OUT_OF_RANGE'
            )), 400
        
        try:
            teds_info = vv_instance.Teds(channel_0based)

            # Format the single channel data using the single channel formatter
            formatted_channel = format_single_channel_teds(teds_info, channel_0based)

            # Prepare result data based on whether we got a transducer or error
            if 'transducer' in formatted_channel:
                result_data = {
                    'transducer': formatted_channel['transducer'],
                    'channel': channel_1based,
                    'success': True
                }
                message = f"Formatted TEDS information retrieved for channel {channel_1based} (1-based)"
            else:  # 'error' in formatted_channel
                result_data = {
                    'error': formatted_channel['error'],
                    'channel': channel_1based,
                    'success': False
                }
                message = f"TEDS error for channel {channel_1based} (1-based): {formatted_channel['error']['error']}"

            return jsonify(success_response(
                result_data,
                message
            ))

        except Exception as e:
            return jsonify(error_response(
                f'Failed to retrieve TEDS for channel {channel_1based}: {str(e)}',
                'TEDS_READ_ERROR'
            )), 500
    
    else:
        # No channel specified - get all TEDS data with formatting
        try:
            teds_info = vv_instance.Teds()

            # Format the data using the formatter
            formatted_data = format_teds_data(teds_info)

            return jsonify(success_response(
                {
                    'result': formatted_data,
                    'channel': 'all',
                    'success': True
                },
                f"Formatted TEDS information retrieved: {len(formatted_data['transducers'])} transducers, {len(formatted_data['errors'])} errors"
            ))

        except Exception as e:
            return jsonify(error_response(
                f'Failed to retrieve TEDS for all channels: {str(e)}',
                'TEDS_READ_ERROR'
            )), 500


@teds_bp.route('/tedsreadandapply', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def teds_read_and_apply(vv_instance):
    """
    Read and Apply TEDS Information for All Channels

    COM Method: TedsReadAndApply()
    Reads and applies TEDS information for all channels on the hardware.
    This operation will automatically configure channels based on their TEDS data.

    No parameters required.

    Example: GET /api/v1/tedsreadandapply or POST /api/v1/tedsreadandapply
    """
    result =  vv_instance.TedsReadAndApply()

    return jsonify(success_response(
        {
            'result': result,
            'success': True
        },
        "TEDS read and apply operation completed successfully for all channels"
    ))


@teds_bp.route('/tedsverifyandapply', methods=['POST'])
@handle_errors
@with_vibrationview
def teds_verify_and_apply(vv_instance):
    """
    Verify and Apply TEDS Information for Specified URNs

    COM Method: TedsVerifyAndApply(urns)
    Verifies and applies TEDS information for the specified URN list.

    Request Body (JSON):
        urns: array - List of URN strings to verify and apply TEDS for

    Example: POST /api/v1/tedsverifyandapply
             Body: {"urns": ["urn1", "urn2", "urn3"]}
    """
    request_data = request.get_json()
    if not request_data:
        return jsonify(error_response(
            'Missing request body - JSON required',
            'MISSING_BODY'
        )), 400

    urns = request_data.get('urns')
    if urns is None:
        return jsonify(error_response(
            'Missing required parameter: urns',
            'MISSING_PARAMETER'
        )), 400

    if not isinstance(urns, list):
        return jsonify(error_response(
            'Parameter "urns" must be an array',
            'INVALID_PARAMETER_TYPE'
        )), 400

    if len(urns) == 0:
        return jsonify(error_response(
            'Parameter "urns" cannot be empty',
            'EMPTY_PARAMETER'
        )), 400

    # Validate URNs are strings
    for i, urn in enumerate(urns):
        if not isinstance(urn, str):
            return jsonify(error_response(
                f'URN at index {i} must be a string, got {type(urn).__name__}',
                'INVALID_URN_TYPE'
            )), 400

    result = vv_instance.TedsVerifyAndApply(urns)

    return jsonify(success_response(
        {
            'result': result,
            'urns': urns,
            'urn_count': len(urns),
            'success': True
        },
        f"TEDS verify and apply operation completed successfully for {len(urns)} URNs"
    ))


@teds_bp.route('/tedsread', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def teds_read(vv_instance):
    """
    Read TEDS Information from Hardware

    COM Method: TedsRead()
    Reads TEDS information from the connected hardware.
    This operation will read the TEDS data from all available channels.

    No parameters required.

    Example: GET /api/v1/tedsread or POST /api/v1/tedsread
    """
    result = vv_instance.TedsRead()

    return jsonify(success_response(
        {
            'result': result,
            'success': True
        },
        "TEDS read operation completed successfully"
    ))


@teds_bp.route('/tedsfromurn', methods=['GET'])
@handle_errors
@with_vibrationview
def teds_from_urn(vv_instance):
    """
    Lookup TEDS Transducer by Unique Registration Number (URN)

    COM Method: TedsFromURN(urn)
    Looks up TEDS transducer information using the specified URN.

    Query Parameters:
        urn: Unique Registration Number string (first positional parameter)

    Example: GET /api/v1/tedsfromurn?urn123456
    """
    # Get URN from query parameters (first parameter after ?)
    query_args = list(request.args.keys())
    if not query_args:
        return jsonify(error_response(
            'Missing required query parameter: urn',
            'MISSING_PARAMETER'
        )), 400

    urn = query_args[0]
    if not urn or not isinstance(urn, str):
        return jsonify(error_response(
            'URN parameter must be a non-empty string',
            'INVALID_PARAMETER'
        )), 400

    result = vv_instance.TedsFromURN(urn)

    # Format the TEDS data using the single channel formatter
    # Use channel index -1 to indicate this is URN-based data (no specific channel)
    formatted_result = format_single_channel_teds(result, -1)

    if 'transducer' in formatted_result:
        return jsonify(success_response(
            {
                'transducer': formatted_result['transducer'],
                'urn': urn,
                'success': True
            },
            f"Formatted TEDS information retrieved for URN: {urn}"
        ))
    else:
        return jsonify(success_response(
            {
                'error': formatted_result['error'],
                'urn': urn,
                'success': False
            },
            f"TEDS error for URN {urn}: {formatted_result['error']['error']}"
        ))


