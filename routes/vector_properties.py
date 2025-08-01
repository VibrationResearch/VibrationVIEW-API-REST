"""
routes/vector_properties.py

Vector properties and metadata methods
- Vector information (units, labels, lengths)
- Channel and control metadata

NOTE: Channel parameters are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface
"""

from flask import Blueprint, request, jsonify
from vibrationviewapi import VibrationVIEW
from .common import handle_errors, success_response, validate_required_params

vector_properties_bp = Blueprint('vector_properties', __name__, url_prefix='/api')

@vector_properties_bp.route('/docs/vector_properties', methods=['GET'])
def vector_properties_docs():
    """Documentation for vector properties endpoints"""
    docs = {
        'module': 'vector_properties',
        'description': 'Vector properties and metadata methods',
        'note': 'Channel parameters use 1-based indexing (user-friendly) and are converted to 0-based for VibrationVIEW COM interface',
        'endpoints': {
            'Vector Properties': {
                'POST /VectorUnit': 'VectorUnit(vectorEnum: int) -> str - Get vector units',
                'POST /VectorLabel': 'VectorLabel(vectorEnum: int) -> str - Get vector label',
                'POST /VectorLength': 'VectorLength(vectorEnum: int) -> int - Get vector array length'
            },
            'Channel Metadata': {
                'POST /ChannelUnit': 'ChannelUnit(channelNum: int) -> str - Get channel units (1-based)',
                'POST /ChannelLabel': 'ChannelLabel(channelNum: int) -> str - Get channel label (1-based)'
            },
            'Control Metadata': {
                'POST /ControlUnit': 'ControlUnit(loopNum: int) -> str - Get control loop units (1-based)',
                'POST /ControlLabel': 'ControlLabel(loopNum: int) -> str - Get control loop label (1-based)'
            }
        },
        'parameter_notes': {
            'channel_indexing': 'Channel parameters (channelNum, loopNum, channel) use 1-based indexing',
            'conversion': 'API automatically converts 1-based user input to 0-based VibrationVIEW COM interface',
            'validation': 'Channel numbers must be >= 1, will return error for channel 0 or negative values'
        }
    }
    return jsonify(docs)

# Vector Properties
@vector_properties_bp.route('/VectorUnit', methods=['POST'])
@handle_errors
def vector_unit():
    """Get units for raw data vector"""
    data = request.get_json()
    error = validate_required_params(data, ['vectorEnum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    with VibrationVIEW() as vv:
        result = vv.VectorUnit(data['vectorEnum'])
    
    return jsonify(success_response({'result': result}))

@vector_properties_bp.route('/VectorLabel', methods=['POST'])
@handle_errors
def vector_label():
    """Get label for raw data vector"""
    data = request.get_json()
    error = validate_required_params(data, ['vectorEnum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    with VibrationVIEW() as vv:
        result = vv.VectorLabel(data['vectorEnum'])
    
    return jsonify(success_response({'result': result}))

@vector_properties_bp.route('/VectorLength', methods=['POST'])
@handle_errors
def vector_length():
    """Get required array length for Raw Data Vector Array"""
    data = request.get_json()
    error = validate_required_params(data, ['vectorEnum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    with VibrationVIEW() as vv:
        result = vv.VectorLength(data['vectorEnum'])
    
    return jsonify(success_response({'result': result}))

# Channel Metadata
@vector_properties_bp.route('/ChannelUnit', methods=['POST'])
@handle_errors
def channel_unit():
    """Get the channel unit associated with channel number (1-based)"""
    data = request.get_json()
    error = validate_required_params(data, ['channelNum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Convert from 1-based to 0-based
    channel_num_1based = data['channelNum']
    if channel_num_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'channelNum must be >= 1 (1-based indexing), got {channel_num_1based}'
        }), 400
    
    channel_num_0based = channel_num_1based - 1
    
    with VibrationVIEW() as vv:
        result = vv.ChannelUnit(channel_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'channelNum': channel_num_1based,
        'internal_channelNum': channel_num_0based
    }))

@vector_properties_bp.route('/ChannelLabel', methods=['POST'])
@handle_errors
def channel_label():
    """Get the channel unit label associated with channel number (1-based)"""
    data = request.get_json()
    error = validate_required_params(data, ['channelNum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Convert from 1-based to 0-based
    channel_num_1based = data['channelNum']
    if channel_num_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'channelNum must be >= 1 (1-based indexing), got {channel_num_1based}'
        }), 400
    
    channel_num_0based = channel_num_1based - 1
    
    with VibrationVIEW() as vv:
        result = vv.ChannelLabel(channel_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'channelNum': channel_num_1based,
        'internal_channelNum': channel_num_0based
    }))

# Control Metadata
@vector_properties_bp.route('/ControlUnit', methods=['POST'])
@handle_errors
def control_unit():
    """Get the channel unit associated with loop number (1-based)"""
    data = request.get_json()
    error = validate_required_params(data, ['loopNum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Convert from 1-based to 0-based
    loop_num_1based = data['loopNum']
    if loop_num_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'loopNum must be >= 1 (1-based indexing), got {loop_num_1based}'
        }), 400
    
    loop_num_0based = loop_num_1based - 1
    
    with VibrationVIEW() as vv:
        result = vv.ControlUnit(loop_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'loopNum': loop_num_1based,
        'internal_loopNum': loop_num_0based
    }))

@vector_properties_bp.route('/ControlLabel', methods=['POST'])
@handle_errors
def control_label():
    """Get the control unit label associated with loop number (1-based)"""
    data = request.get_json()
    error = validate_required_params(data, ['loopNum'])
    if error:
        return jsonify({'success': False, 'error': error}), 400
    
    # Convert from 1-based to 0-based
    loop_num_1based = data['loopNum']
    if loop_num_1based < 1:
        return jsonify({
            'success': False, 
            'error': f'loopNum must be >= 1 (1-based indexing), got {loop_num_1based}'
        }), 400
    
    loop_num_0based = loop_num_1based - 1
    
    with VibrationVIEW() as vv:
        result = vv.ControlLabel(loop_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'loopNum': loop_num_1based,
        'internal_loopNum': loop_num_0based
    }))