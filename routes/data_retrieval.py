# ============================================================================
# FILE: routes/data_retrieval.py (Data Retrieval Routes)
# ============================================================================

"""
Data Retrieval Routes - 1:1 VibrationVIEW COM Interface Mapping
Real-time data access operations matching exact COM method signatures
Channel and loop parameters use 1-based indexing (user-friendly)

Includes:
- Primary data arrays (demand, control, channel, output)
- Vector data retrieval
- Vector properties and metadata
- Channel and control metadata
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging

# Create blueprint
data_retrieval_bp = Blueprint('data_retrieval', __name__)

logger = logging.getLogger(__name__)

# ============================================================================
# DOCUMENTATION ENDPOINTS
# ============================================================================

@data_retrieval_bp.route('/docs/vector_enums', methods=['GET'])
def get_vector_enumerations():
    """Get complete vector enumeration reference"""
    enums = {
        'module': 'vector_enumerations',
        'description': 'Complete VibrationVIEW vector enumeration reference for Vector() method',
        'waveform_enums': {
            'VV_WAVEFORMAXIS': 0,
            'VV_WAVEFORM1': 1, 'VV_WAVEFORM2': 2, 'VV_WAVEFORM3': 3, 'VV_WAVEFORM4': 4,
            'VV_WAVEFORM5': 5, 'VV_WAVEFORM6': 6, 'VV_WAVEFORM7': 7, 'VV_WAVEFORM8': 8,
            'VV_WAVEFORM9': 9, 'VV_WAVEFORM10': 10, 'VV_WAVEFORM11': 11, 'VV_WAVEFORM12': 12,
            'VV_WAVEFORM13': 13, 'VV_WAVEFORM14': 14, 'VV_WAVEFORM15': 15, 'VV_WAVEFORM16': 16,
            'VV_WAVEFORM17': 17, 'VV_WAVEFORM18': 18, 'VV_WAVEFORM19': 19, 'VV_WAVEFORM20': 20,
            'VV_WAVEFORM21': 21, 'VV_WAVEFORM22': 22, 'VV_WAVEFORM23': 23, 'VV_WAVEFORM24': 24,
            'VV_WAVEFORM25': 25, 'VV_WAVEFORM26': 26, 'VV_WAVEFORM27': 27, 'VV_WAVEFORM28': 28,
            'VV_WAVEFORM29': 29, 'VV_WAVEFORM30': 30, 'VV_WAVEFORM31': 31, 'VV_WAVEFORM32': 32,
            'VV_WAVEFORM33': 33, 'VV_WAVEFORM34': 34, 'VV_WAVEFORM35': 35, 'VV_WAVEFORM36': 36,
            'VV_WAVEFORM37': 37, 'VV_WAVEFORM38': 38, 'VV_WAVEFORM39': 39, 'VV_WAVEFORM40': 40,
            'VV_WAVEFORM41': 41, 'VV_WAVEFORM42': 42, 'VV_WAVEFORM43': 43, 'VV_WAVEFORM44': 44,
            'VV_WAVEFORM45': 45, 'VV_WAVEFORM46': 46, 'VV_WAVEFORM47': 47, 'VV_WAVEFORM48': 48,
            'VV_WAVEFORM49': 49, 'VV_WAVEFORM50': 50, 'VV_WAVEFORM51': 51, 'VV_WAVEFORM52': 52,
            'VV_WAVEFORM53': 53, 'VV_WAVEFORM54': 54, 'VV_WAVEFORM55': 55, 'VV_WAVEFORM56': 56,
            'VV_WAVEFORM57': 57, 'VV_WAVEFORM58': 58, 'VV_WAVEFORM59': 59, 'VV_WAVEFORM60': 60,
            'VV_WAVEFORM61': 61, 'VV_WAVEFORM62': 62, 'VV_WAVEFORM63': 63, 'VV_WAVEFORM64': 64,
            'VV_WAVEFORMDEMAND': 90, 'VV_WAVEFORMCONTROL': 91,
            'VV_WAVEFORMDEMAND2': 92, 'VV_WAVEFORMCONTROL2': 93,
            'VV_WAVEFORMDEMAND3': 94, 'VV_WAVEFORMCONTROL3': 95,
            'VV_WAVEFORMDEMAND4': 96, 'VV_WAVEFORMCONTROL4': 97
        },
        'frequency_enums': {
            'VV_FREQUENCYAXIS': 100,
            'VV_FREQUENCY1': 101, 'VV_FREQUENCY2': 102, 'VV_FREQUENCY3': 103, 'VV_FREQUENCY4': 104,
            'VV_FREQUENCY5': 105, 'VV_FREQUENCY6': 106, 'VV_FREQUENCY7': 107, 'VV_FREQUENCY8': 108,
            'VV_FREQUENCY9': 109, 'VV_FREQUENCY10': 110, 'VV_FREQUENCY11': 111, 'VV_FREQUENCY12': 112,
            'VV_FREQUENCY13': 113, 'VV_FREQUENCY14': 114, 'VV_FREQUENCY15': 115, 'VV_FREQUENCY16': 116,
            'VV_FREQUENCY17': 117, 'VV_FREQUENCY18': 118, 'VV_FREQUENCY19': 119, 'VV_FREQUENCY20': 120,
            'VV_FREQUENCY21': 121, 'VV_FREQUENCY22': 122, 'VV_FREQUENCY23': 123, 'VV_FREQUENCY24': 124,
            'VV_FREQUENCY25': 125, 'VV_FREQUENCY26': 126, 'VV_FREQUENCY27': 127, 'VV_FREQUENCY28': 128,
            'VV_FREQUENCY29': 129, 'VV_FREQUENCY30': 130, 'VV_FREQUENCY31': 131, 'VV_FREQUENCY32': 132,
            'VV_FREQUENCY33': 133, 'VV_FREQUENCY34': 134, 'VV_FREQUENCY35': 135, 'VV_FREQUENCY36': 136,
            'VV_FREQUENCY37': 137, 'VV_FREQUENCY38': 138, 'VV_FREQUENCY39': 139, 'VV_FREQUENCY40': 140,
            'VV_FREQUENCY41': 141, 'VV_FREQUENCY42': 142, 'VV_FREQUENCY43': 143, 'VV_FREQUENCY44': 144,
            'VV_FREQUENCY45': 145, 'VV_FREQUENCY46': 146, 'VV_FREQUENCY47': 147, 'VV_FREQUENCY48': 148,
            'VV_FREQUENCY49': 149, 'VV_FREQUENCY50': 150, 'VV_FREQUENCY51': 151, 'VV_FREQUENCY52': 152,
            'VV_FREQUENCY53': 153, 'VV_FREQUENCY54': 154, 'VV_FREQUENCY55': 155, 'VV_FREQUENCY56': 156,
            'VV_FREQUENCY57': 157, 'VV_FREQUENCY58': 158, 'VV_FREQUENCY59': 159, 'VV_FREQUENCY60': 160,
            'VV_FREQUENCY61': 161, 'VV_FREQUENCY62': 162, 'VV_FREQUENCY63': 163, 'VV_FREQUENCY64': 164,
            'VV_FREQUENCYDRIVE': 180, 'VV_FREQUENCYRESPONSE': 181,
            'VV_FREQUENCYDRIVE2': 182, 'VV_FREQUENCYRESPONSE2': 183,
            'VV_FREQUENCYDRIVE3': 184, 'VV_FREQUENCYRESPONSE3': 185,
            'VV_FREQUENCYDRIVE4': 186, 'VV_FREQUENCYRESPONSE4': 187,
            'VV_FREQUENCYDEMAND': 190, 'VV_FREQUENCYCONTROL': 191,
            'VV_FREQUENCYDEMAND2': 192, 'VV_FREQUENCYCONTROL2': 193,
            'VV_FREQUENCYDEMAND3': 194, 'VV_FREQUENCYCONTROL3': 195,
            'VV_FREQUENCYDEMAND4': 196, 'VV_FREQUENCYCONTROL4': 197
        },
        'time_history_enums': {
            'VV_TIMEHISTORYAXIS': 200,
            'VV_REARINPUTHISTORY1': 301, 'VV_REARINPUTHISTORY2': 302, 'VV_REARINPUTHISTORY3': 303, 'VV_REARINPUTHISTORY4': 304,
            'VV_REARINPUTHISTORY5': 305, 'VV_REARINPUTHISTORY6': 306, 'VV_REARINPUTHISTORY7': 307, 'VV_REARINPUTHISTORY8': 308,
            'VV_REARINPUTHISTORY9': 309, 'VV_REARINPUTHISTORY10': 310, 'VV_REARINPUTHISTORY11': 311, 'VV_REARINPUTHISTORY12': 312,
            'VV_REARINPUTHISTORY13': 313, 'VV_REARINPUTHISTORY14': 314, 'VV_REARINPUTHISTORY15': 315, 'VV_REARINPUTHISTORY16': 316,
            'VV_REARINPUTHISTORY17': 317, 'VV_REARINPUTHISTORY18': 318, 'VV_REARINPUTHISTORY19': 319, 'VV_REARINPUTHISTORY20': 320,
            'VV_REARINPUTHISTORY21': 321, 'VV_REARINPUTHISTORY22': 322, 'VV_REARINPUTHISTORY23': 323, 'VV_REARINPUTHISTORY24': 324,
            'VV_REARINPUTHISTORY25': 325, 'VV_REARINPUTHISTORY26': 326, 'VV_REARINPUTHISTORY27': 327, 'VV_REARINPUTHISTORY28': 328,
            'VV_REARINPUTHISTORY29': 329, 'VV_REARINPUTHISTORY30': 330, 'VV_REARINPUTHISTORY31': 331, 'VV_REARINPUTHISTORY32': 332,
            'VV_REARINPUTHISTORY33': 333, 'VV_REARINPUTHISTORY34': 334, 'VV_REARINPUTHISTORY35': 335, 'VV_REARINPUTHISTORY36': 336,
            'VV_REARINPUTHISTORY37': 337, 'VV_REARINPUTHISTORY38': 338, 'VV_REARINPUTHISTORY39': 339, 'VV_REARINPUTHISTORY40': 340,
            'VV_REARINPUTHISTORY41': 341, 'VV_REARINPUTHISTORY42': 342, 'VV_REARINPUTHISTORY43': 343, 'VV_REARINPUTHISTORY44': 344,
            'VV_REARINPUTHISTORY45': 345, 'VV_REARINPUTHISTORY46': 346, 'VV_REARINPUTHISTORY47': 347, 'VV_REARINPUTHISTORY48': 348,
            'VV_REARINPUTHISTORY49': 349, 'VV_REARINPUTHISTORY50': 350, 'VV_REARINPUTHISTORY51': 351, 'VV_REARINPUTHISTORY52': 352,
            'VV_REARINPUTHISTORY53': 353, 'VV_REARINPUTHISTORY54': 354, 'VV_REARINPUTHISTORY55': 355, 'VV_REARINPUTHISTORY56': 356,
            'VV_REARINPUTHISTORY57': 357, 'VV_REARINPUTHISTORY58': 358, 'VV_REARINPUTHISTORY59': 359, 'VV_REARINPUTHISTORY60': 360,
            'VV_REARINPUTHISTORY61': 361, 'VV_REARINPUTHISTORY62': 362, 'VV_REARINPUTHISTORY63': 363, 'VV_REARINPUTHISTORY64': 364
        },
        'usage_examples': {
            'waveform_data': {
                'channel_1_waveform': 'GET /api/vector?vectorenum=1',
                'channel_10_waveform': 'GET /api/vector?vectorenum=10',
                'waveform_time_axis': 'GET /api/vector?vectorenum=0',
                'demand_waveform': 'GET /api/vector?vectorenum=90',
                'control_waveform': 'GET /api/vector?vectorenum=91'
            },
            'frequency_data': {
                'channel_1_frequency': 'GET /api/vector?vectorenum=101',
                'channel_20_frequency': 'GET /api/vector?vectorenum=120',
                'frequency_axis': 'GET /api/vector?vectorenum=100',
                'drive_frequency': 'GET /api/vector?vectorenum=180',
                'response_frequency': 'GET /api/vector?vectorenum=181'
            },
            'time_history_data': {
                'rear_input_1_history': 'GET /api/vector?vectorenum=301',
                'rear_input_32_history': 'GET /api/vector?vectorenum=332',
                'time_history_axis': 'GET /api/vector?vectorenum=200'
            }
        },
        'notes': [
            'All vector enumerations correspond to specific data types in VibrationVIEW',
            'Waveform vectors (1-64) provide time-domain data for input channels',
            'Frequency vectors (101-164) provide frequency-domain data for input channels',
            'Rear input history vectors (301-364) provide time history for auxiliary inputs',
            'Axis vectors (0, 100, 200) provide corresponding axis data for plotting',
            'Control/Demand vectors provide waveform and frequency data for output loops',
            'Drive/Response vectors provide frequency response analysis data',
            'Vector availability depends on test type and hardware configuration'
        ]
    }
    return jsonify(enums)

@data_retrieval_bp.route('/docs/data_retrieval', methods=['GET'])
def get_documentation():
    """Get data retrieval module documentation"""
    docs = {
        'module': 'data_retrieval',
        'description': '1:1 mapping of VibrationVIEW COM data retrieval methods including vector properties',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Primary Data Arrays': {
                'GET /demand': {
                    'description': 'Get demand values for all loops',
                    'com_method': 'Demand()',
                    'parameters': 'None',
                    'returns': 'List[float] - Demand values for each output loop'
                },
                'GET /control': {
                    'description': 'Get control values for all loops',
                    'com_method': 'Control()',
                    'parameters': 'None',
                    'returns': 'List[float] - Control values for each output loop'
                },
                'GET /channel': {
                    'description': 'Get channel values for all channels',
                    'com_method': 'Channel()',
                    'parameters': 'None',
                    'returns': 'List[float] - Channel values for all input channels'
                },
                'GET /output': {
                    'description': 'Get output values for all loops',
                    'com_method': 'Output()',
                    'parameters': 'None',
                    'returns': 'List[float] - Output values for each output loop'
                }
            },
            'Vector Data': {
                'GET /vector': {
                    'description': 'Get raw data vector',
                    'com_method': 'Vector(vectorenum, columns)',
                    'parameters': {
                        'vectorenum': 'integer - Vector enumeration identifier (required query parameter)',
                        'columns': 'integer - Number of columns (optional query parameter, default: 1)'
                    },
                    'returns': 'List[List[float]] - Raw data vector array',
                    'examples': [
                        'GET /api/vector?vectorenum=1',
                        'GET /api/vector?vectorenum=2&columns=4'
                    ]
                }
            },
            'Vector Properties': {
                'GET /vectorunit': {
                    'description': 'Get vector units',
                    'com_method': 'VectorUnit(vectorenum)',
                    'parameters': {'vectorenum': 'integer - Vector enumeration identifier (query parameter)'},
                    'returns': 'str - Units for the vector',
                    'example': 'GET /api/vectorunit?vectorenum=1'
                },
                'GET /vectorlabel': {
                    'description': 'Get vector label',
                    'com_method': 'VectorLabel(vectorenum)',
                    'parameters': {'vectorenum': 'integer - Vector enumeration identifier (query parameter)'},
                    'returns': 'str - Label for the vector',
                    'example': 'GET /api/vectorlabel?vectorenum=2'
                },
                'GET /vectorlength': {
                    'description': 'Get vector array length',
                    'com_method': 'VectorLength(vectorenum)',
                    'parameters': {'vectorenum': 'integer - Vector enumeration identifier (query parameter)'},
                    'returns': 'int - Required array length for the vector',
                    'example': 'GET /api/vectorlength?vectorenum=3'
                }
            },
            'Channel Metadata (1-based indexing)': {
                'GET /channelunit': {
                    'description': 'Get channel units',
                    'com_method': 'ChannelUnit(channelnum - 1)',
                    'parameters': {'channelnum': 'integer - Channel number (1-based, converted to 0-based internally, query parameter)'},
                    'returns': 'str - Units for the channel',
                    'example': 'GET /api/channelunit?channelnum=3'
                },
                'GET /channellabel': {
                    'description': 'Get channel label',
                    'com_method': 'ChannelLabel(channelnum - 1)',
                    'parameters': {'channelnum': 'integer - Channel number (1-based, converted to 0-based internally, query parameter)'},
                    'returns': 'str - Label for the channel',
                    'example': 'GET /api/channellabel?channelnum=1'
                }
            },
            'Control Metadata (1-based indexing)': {
                'GET /controlunit': {
                    'description': 'Get control loop units',
                    'com_method': 'ControlUnit(loopnum - 1)',
                    'parameters': {'loopnum': 'integer - Loop number (1-based, converted to 0-based internally, query parameter)'},
                    'returns': 'str - Units for the control loop',
                    'example': 'GET /api/controlunit?loopnum=2'
                },
                'GET /controllabel': {
                    'description': 'Get control loop label',
                    'com_method': 'ControlLabel(loopnum - 1)',
                    'parameters': {'loopnum': 'integer - Loop number (1-based, converted to 0-based internally, query parameter)'},
                    'returns': 'str - Label for the control loop',
                    'example': 'GET /api/controllabel?loopnum=4'
                }
            }
        },
        'indexing_notes': {
            'channel_parameters': 'Channel and loop parameters use 1-based indexing for user convenience',
            'internal_conversion': 'API automatically converts 1-based input to 0-based for VibrationVIEW COM interface',
            'validation': 'Channel/loop numbers must be >= 1, will return error for 0 or negative values',
            'vector_enums': 'Vector enumerations are passed as-is (no conversion needed)'
        },
        'notes': [
            'All methods return real-time data from VibrationVIEW',
            'Array sizes depend on hardware configuration',
            'Channel arrays based on input channel count',
            'Control/Demand/Output arrays based on output loop count',
            'Vector data requires valid vectorenum identifier from the enumerations',
            'Arrays use 0-based indexing internally but returned in order (channel 1 = index 0, etc.)',
            'Channel and loop parameters use 1-based indexing and are converted internally',
            'Vector enumerations are used directly without conversion'
        ]
    }
    return jsonify(docs)

# ============================================================================
# PRIMARY DATA ARRAYS
# ============================================================================

@data_retrieval_bp.route('/demand', methods=['GET'])
@handle_errors
@with_vibrationview
def demand(vv_instance):
    """
    Get demand values for all loops
    
    COM Method: Demand()
    Returns the demand values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Demand()
    
    return jsonify(success_response(
        {'result': result},
        f"Retrieved {len(result)} demand values"
    ))

@data_retrieval_bp.route('/control', methods=['GET'])
@handle_errors
@with_vibrationview
def control(vv_instance):
    """
    Get control values for all loops
    
    COM Method: Control()
    Returns the control values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Control()
    
    return jsonify(success_response(
        {'result': result},
        f"Retrieved {len(result)} control values"
    ))

@data_retrieval_bp.route('/channel', methods=['GET'])
@handle_errors
@with_vibrationview
def channel(vv_instance):
    """
    Get channel values for all channels
    
    COM Method: Channel()
    Returns the channel values for all input channels.
    Array returned in order: [channel1, channel2, channel3, ...] (1-based channel numbering for reference)
    """
    result = vv_instance.Channel()
    
    return jsonify(success_response(
        {'result': result},
        f"Retrieved {len(result)} channel values"
    ))

@data_retrieval_bp.route('/output', methods=['GET'])
@handle_errors
@with_vibrationview
def output(vv_instance):
    """
    Get output values for all loops
    
    COM Method: Output()
    Returns the output values for each output loop.
    Array returned in order: [loop1, loop2, loop3, ...] (1-based loop numbering for reference)
    """
    result = vv_instance.Output()
    
    return jsonify(success_response(
        {'result': result},
        f"Retrieved {len(result)} output values"
    ))

# ============================================================================
# VECTOR DATA
# ============================================================================

@data_retrieval_bp.route('/vector', methods=['GET'])
@handle_errors
@with_vibrationview
def vector(vv_instance):
    """
    Get raw data vector
    
    COM Method: Vector(vectorenum, columns)
    Returns raw data vector array for the specified vector enumeration.
    
    Query Parameters:
        vectorenum: Vector enumeration identifier (required)
        columns: Number of columns (optional, default: 1)
    
    Examples:
        GET /api/vector?vectorenum=1
        GET /api/vector?vectorenum=2&columns=4
    """
    vectorenum = request.args.get('vectorenum', type=int)
    if vectorenum is None:
        return jsonify(error_response(
            'Missing required query parameter: vectorenum',
            'MISSING_PARAMETER'
        )), 400
    
    columns = request.args.get('columns', type=int, default=1)
    
    # Validate columns parameter
    if columns < 1:
        return jsonify(error_response(
            f'columns must be >= 1, got {columns}',
            'INVALID_PARAMETER'
        )), 400
    
    try:
        result = vv_instance.Vector(vectorenum, columns)
        
        return jsonify(success_response(
            {
                'result': result,
                'vectorenum': vectorenum,
                'columns': columns,
                'rows': len(result) if result else 0
            },
            f"Retrieved vector data for vectorenum {vectorenum} with {columns} columns"
        ))
        
    except Exception as e:
        return jsonify(error_response(
            f'Failed to retrieve vector data: {str(e)}',
            'VECTOR_READ_ERROR'
        )), 500

# ============================================================================
# VECTOR PROPERTIES
# ============================================================================

@data_retrieval_bp.route('/vectorunit', methods=['GET'])
@handle_errors
@with_vibrationview
def vector_unit(vv_instance):
    """
    Get units for raw data vector
    
    COM Method: VectorUnit(vectorenum)
    Returns the units string for the specified vector enumeration.
    
    Query Parameters:
        vectorenum: Vector enumeration identifier (required)
    
    Example:
        GET /api/vectorunit?vectorenum=1
    """
    vectorenum = request.args.get('vectorenum', type=int)
    if vectorenum is None:
        return jsonify(error_response(
            'Missing required query parameter: vectorenum',
            'MISSING_PARAMETER'
        )), 400
    
    result = vv_instance.VectorUnit(vectorenum)
    
    return jsonify(success_response({
        'result': result,
        'vectorenum': vectorenum
    }))

@data_retrieval_bp.route('/vectorlabel', methods=['GET'])
@handle_errors
@with_vibrationview
def vector_label(vv_instance):
    """
    Get label for raw data vector
    
    COM Method: VectorLabel(vectorenum)
    Returns the label string for the specified vector enumeration.
    
    Query Parameters:
        vectorenum: Vector enumeration identifier (required)
    
    Example:
        GET /api/vectorlabel?vectorenum=2
    """
    vectorenum = request.args.get('vectorenum', type=int)
    if vectorenum is None:
        return jsonify(error_response(
            'Missing required query parameter: vectorenum',
            'MISSING_PARAMETER'
        )), 400
    
    result = vv_instance.VectorLabel(vectorenum)
    
    return jsonify(success_response({
        'result': result,
        'vectorenum': vectorenum
    }))

@data_retrieval_bp.route('/vectorlength', methods=['GET'])
@handle_errors
@with_vibrationview
def vector_length(vv_instance):
    """
    Get required array length for Raw Data Vector Array
    
    COM Method: VectorLength(vectorenum)
    Returns the required array length for the specified vector enumeration.
    
    Query Parameters:
        vectorenum: Vector enumeration identifier (required)
    
    Example:
        GET /api/vectorlength?vectorenum=3
    """
    vectorenum = request.args.get('vectorenum', type=int)
    if vectorenum is None:
        return jsonify(error_response(
            'Missing required query parameter: vectorenum',
            'MISSING_PARAMETER'
        )), 400
    
    result = vv_instance.VectorLength(vectorenum)
    
    return jsonify(success_response({
        'result': result,
        'vectorenum': vectorenum
    }))

# ============================================================================
# CHANNEL METADATA (1-based indexing with conversion)
# ============================================================================

@data_retrieval_bp.route('/channelunit', methods=['GET'])
@handle_errors
@with_vibrationview
def channel_unit(vv_instance):
    """
    Get the channel unit associated with channel number (1-based)
    
    COM Method: ChannelUnit(channelnum - 1)
    Channel numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.
    
    Query Parameters:
        channelnum: Channel number (1-based, required)
    
    Example:
        GET /api/channelunit?channelnum=3
    """
    channelnum = request.args.get('channelnum', type=int)
    if channelnum is None:
        return jsonify(error_response(
            'Missing required query parameter: channelnum',
            'MISSING_PARAMETER'
        )), 400
    
    # Convert from 1-based to 0-based
    if channelnum < 1:
        return jsonify(error_response(
            f'channelnum must be >= 1 (1-based indexing), got {channelnum}',
            'INVALID_PARAMETER'
        )), 400
    
    channel_num_0based = channelnum - 1
    
    result = vv_instance.ChannelUnit(channel_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'channelnum': channelnum,
        'internal_channelnum': channel_num_0based
    }))

@data_retrieval_bp.route('/channellabel', methods=['GET'])
@handle_errors
@with_vibrationview
def channel_label(vv_instance):
    """
    Get the channel unit label associated with channel number (1-based)
    
    COM Method: ChannelLabel(channelnum - 1)
    Channel numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.
    
    Query Parameters:
        channelnum: Channel number (1-based, required)
    
    Example:
        GET /api/channellabel?channelnum=1
    """
    channelnum = request.args.get('channelnum', type=int)
    if channelnum is None:
        return jsonify(error_response(
            'Missing required query parameter: channelnum',
            'MISSING_PARAMETER'
        )), 400
    
    # Convert from 1-based to 0-based
    if channelnum < 1:
        return jsonify(error_response(
            f'channelnum must be >= 1 (1-based indexing), got {channelnum}',
            'INVALID_PARAMETER'
        )), 400
    
    channel_num_0based = channelnum - 1
    
    result = vv_instance.ChannelLabel(channel_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'channelnum': channelnum,
        'internal_channelnum': channel_num_0based
    }))

# ============================================================================
# CONTROL METADATA (1-based indexing with conversion)
# ============================================================================

@data_retrieval_bp.route('/controlunit', methods=['GET'])
@handle_errors
@with_vibrationview
def control_unit(vv_instance):
    """
    Get the channel unit associated with loop number (1-based)
    
    COM Method: ControlUnit(loopnum - 1)
    Loop numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.
    
    Query Parameters:
        loopnum: Loop number (1-based, required)
    
    Example:
        GET /api/controlunit?loopnum=2
    """
    loopnum = request.args.get('loopnum', type=int)
    if loopnum is None:
        return jsonify(error_response(
            'Missing required query parameter: loopnum',
            'MISSING_PARAMETER'
        )), 400
    
    # Convert from 1-based to 0-based
    if loopnum < 1:
        return jsonify(error_response(
            f'loopnum must be >= 1 (1-based indexing), got {loopnum}',
            'INVALID_PARAMETER'
        )), 400
    
    loop_num_0based = loopnum - 1
    
    result = vv_instance.ControlUnit(loop_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'loopnum': loopnum,
        'internal_loopnum': loop_num_0based
    }))

@data_retrieval_bp.route('/controllabel', methods=['GET'])
@handle_errors
@with_vibrationview
def control_label(vv_instance):
    """
    Get the control unit label associated with loop number (1-based)
    
    COM Method: ControlLabel(loopnum - 1)
    Loop numbers are 1-based for user convenience but converted to 0-based for VibrationVIEW COM interface.
    
    Query Parameters:
        loopnum: Loop number (1-based, required)
    
    Example:
        GET /api/controllabel?loopnum=4
    """
    loopnum = request.args.get('loopnum', type=int)
    if loopnum is None:
        return jsonify(error_response(
            'Missing required query parameter: loopnum',
            'MISSING_PARAMETER'
        )), 400
    
    # Convert from 1-based to 0-based
    if loopnum < 1:
        return jsonify(error_response(
            f'loopnum must be >= 1 (1-based indexing), got {loopnum}',
            'INVALID_PARAMETER'
        )), 400
    
    loop_num_0based = loopnum - 1
    
    result = vv_instance.ControlLabel(loop_num_0based)
    
    return jsonify(success_response({
        'result': result,
        'loopnum': loopnum,
        'internal_loopnum': loop_num_0based
    }))