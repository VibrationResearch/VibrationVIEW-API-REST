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
                    'example': 'GET /api/inputtedschannel?3 (channel 3, 1-based)'
                },
                'GET /teds': {
                    'description': 'Get formatted TEDS information for specific channel or all channels',
                    'com_method': 'Teds(channel) or Teds()',
                    'parameters': {
                        'channel': 'int - Optional channel number (1-based, first query parameter)'
                    },
                    'returns': 'object - Structured transducer data for specific channel or transducers/errors arrays for all channels',
                    'examples': [
                        'GET /api/teds (all channels - transducers/errors arrays)',
                        'GET /api/teds?3 (channel 3, 1-based - single transducer object)'
                    ]
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
    
    Example: GET /api/inputtedschannel?3 (gets channel 3, 1-based)
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

@teds_bp.route('/Teds', methods=['GET'])
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
        GET /api/Teds (all channels)
        GET /api/Teds?3 (channel 3, 1-based)
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
    
    else:
        # No channel specified - get all TEDS data
        try:
            teds_info = vv_instance.Teds()
            
            return jsonify(success_response(
                {
                    'result': teds_info,
                    'channel': 'all',
                    'success': True
                },
                "TEDS information retrieved for all channels"
            ))
            
        except Exception as e:
            return jsonify(error_response(
                f'Failed to retrieve TEDS for all channels: {str(e)}',
                'TEDS_READ_ERROR'
            )), 500