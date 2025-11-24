# ============================================================================
# FILE: routes/aux_inputs.py
# ============================================================================

"""
routes/aux_inputs.py

Auxiliary input properties and metadata methods
- Rear input channel metadata (1-based indexing)
"""

from flask import Blueprint, request, jsonify
from vibrationviewapi import VibrationVIEW
from utils.vv_manager import with_vibrationview
from .common import handle_errors, success_response, validate_required_params

auxinputs_bp = Blueprint('auxinputs', __name__, url_prefix='/api')

@auxinputs_bp.route('/docs/auxinputs', methods=['GET'])
def auxinputs_docs():
    """Documentation for auxiliary inputs endpoints"""
    docs = {
        'module': 'auxinputs',
        'description': 'Auxiliary input properties and metadata methods',
        'note': 'Channel parameters use 1-based indexing (user-friendly) and are converted to 0-based for VibrationVIEW COM interface',
        'endpoints': {
            'Rear Input Data': {
                'GET /rearinput': 'RearInput() -> List[float] - Get rear input values for all channels'
            },
            'Rear Input Metadata': {
                'GET /rearinputunit?channel=<int>': 'RearInputUnit(channel: int) -> str - Get rear input units (1-based)',
                'GET /rearinputunit?<int>': 'RearInputUnit(channel: int) -> str - Get rear input units using unnamed parameter (1-based)',
                'GET /rearinputlabel?channel=<int>': 'RearInputLabel(channel: int) -> str - Get rear input label (1-based)',
                'GET /rearinputlabel?<int>': 'RearInputLabel(channel: int) -> str - Get rear input label using unnamed parameter (1-based)'
            }
        },
        'parameter_notes': {
            'channel_indexing': 'Channel parameters use 1-based indexing',
            'conversion': 'API automatically converts 1-based user input to 0-based VibrationVIEW COM interface',
            'validation': 'Channel numbers must be >= 1, will return error for channel 0 or negative values'
        }
    }
    return jsonify(docs)

@auxinputs_bp.route('/rearinput', methods=['GET'])
@handle_errors
@with_vibrationview
def rear_input(vv_instance):
    """
    Get Rear Input Values for All Channels

    COM Method: RearInput()
    Returns the rear input values for all auxiliary input channels.
    Array returned in order: [channel1, channel2, channel3, ...] (1-based channel numbering for reference)
    """
    result = vv_instance.RearInput()

    return jsonify(success_response({
        'result': result
    }, f"Retrieved {len(result)} rear input values"))

@auxinputs_bp.route('/rearinputunit', methods=['GET'])
@handle_errors
@with_vibrationview
def rear_input_unit(vv_instance):
    """Get units for the rear input channel (1-based indexing)"""
    # Get channel from 'channel' parameter or first unnamed parameter
    channel_1based = request.args.get('channel', type=int)
    
    # If no 'channel' parameter, try to get the first unnamed parameter
    if channel_1based is None:
        args = list(request.args.keys())
        if args and args[0].replace('-', '').isdigit():
            try:
                channel_1based = int(args[0])
            except ValueError:
                pass
    
    if channel_1based is None:
        return jsonify({
            'success': False, 
            'error': 'Missing required parameter: channel (or unnamed numeric parameter)'
        }), 400
    
    # Validate 1-based channel number
    if channel_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'channel must be >= 1 (1-based indexing), got {channel_1based}'
        }), 400
    
    # Convert from 1-based to 0-based
    channel_0based = channel_1based - 1
    
    result = vv_instance.RearInputUnit(channel_0based)
    
    return jsonify(success_response({
        'result': result,
        'channel': channel_1based,
        'internal_channel': channel_0based
    }))

@auxinputs_bp.route('/rearinputlabel', methods=['GET'])
@handle_errors
@with_vibrationview
def rear_input_label(vv_instance):
    """Get label for the rear input channel (1-based indexing)"""
    # Get channel from 'channel' parameter or first unnamed parameter
    channel_1based = request.args.get('channel', type=int)
    
    # If no 'channel' parameter, try to get the first unnamed parameter
    if channel_1based is None:
        args = list(request.args.keys())
        if args and args[0].replace('-', '').isdigit():
            try:
                channel_1based = int(args[0])
            except ValueError:
                pass
    
    if channel_1based is None:
        return jsonify({
            'success': False, 
            'error': 'Missing required parameter: channel (or unnamed numeric parameter)'
        }), 400
    
    # Validate 1-based channel number
    if channel_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'channel must be >= 1 (1-based indexing), got {channel_1based}'
        }), 400
    
    # Convert from 1-based to 0-based
    channel_0based = channel_1based - 1
    
    result = vv_instance.RearInputLabel(channel_0based)
    
    return jsonify(success_response({
        'result': result,
        'channel': channel_1based,
        'internal_channel': channel_0based
    }))