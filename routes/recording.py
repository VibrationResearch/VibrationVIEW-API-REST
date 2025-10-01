# ============================================================================
# FILE: routes/recording.py (Recording Control Routes) - Updated
# ============================================================================

"""
Recording Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Recording operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import extract_com_error_info

import logging
from datetime import datetime

# Create blueprint
recording_bp = Blueprint('recording', __name__)

logger = logging.getLogger(__name__)

@recording_bp.route('/docs/recording', methods=['GET'])
def get_documentation():
    """Get recording control module documentation"""
    docs = {
        'module': 'recording',
        'description': '1:1 mapping of VibrationVIEW COM recording control methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'GET|POST /recordstart': {
                'description': 'Start recording data',
                'com_method': 'RecordStart()',
                'parameters': 'None',
                'returns': 'Result from RecordStart()',
                'example': 'GET /api/recordstart or POST /api/recordstart'
            },
            'GET|POST /recordstop': {
                'description': 'Stop recording data',
                'com_method': 'RecordStop()',
                'parameters': 'None',
                'returns': 'Result from RecordStop()',
                'example': 'GET /api/recordstop or POST /api/recordstop'
            },
            'GET|POST /recordpause': {
                'description': 'Pause recording data',
                'com_method': 'RecordPause()',
                'parameters': 'None',
                'returns': 'Result from RecordPause()',
                'example': 'GET /api/recordpause or POST /api/recordpause'
            },
            'GET /recordgetfilename': {
                'description': 'Get the last recording filename',
                'com_method': 'RecordGetFilename()',
                'parameters': 'None',
                'returns': 'string - Last recording filename'
            }
        },
        'notes': [
            'Recording methods return boolean status indicating success/failure',
            'RecordGetFilename returns the filename of the last completed recording',
            'GetActiveTest returns the currently loaded test object',
            'If COM method raises exception, it will be caught and returned as error',
            'Recording operations require a test to be loaded and running',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

@recording_bp.route('/recordstart', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def record_start(vv_instance):
    """
    Start Recording Data

    COM Method: RecordStart()
    Begins recording data from the currently running test.
    Test must be loaded and running before recording can start.
    """
    result = vv_instance.RecordStart()

    return jsonify(success_response(
        {'result': result},
        "RecordStart command executed"
    ))

@recording_bp.route('/recordstop', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def record_stop(vv_instance):
    """
    Stop Recording Data

    COM Method: RecordStop()
    Stops the current data recording session.
    """
    result = vv_instance.RecordStop()

    return jsonify(success_response(
        {'result': result},
        "RecordStop command executed"
    ))

@recording_bp.route('/recordpause', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def record_pause(vv_instance):
    """
    Pause Recording Data

    COM Method: RecordPause()
    Pauses the current data recording session.
    Recording can be resumed with RecordStart.
    """
    result = vv_instance.RecordPause()

    return jsonify(success_response(
        {'result': result},
        "RecordPause command executed"
    ))

@recording_bp.route('/recordgetfilename', methods=['GET'])
@handle_errors
@with_vibrationview
def record_get_filename(vv_instance):
    """
    Get Last Recording Filename
    
    COM Method: RecordGetFilename()
    Returns the filename of the last completed recording.
    """
    result = vv_instance.RecordGetFilename()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"RecordGetFilename executed successfully: {result}"
    ))

@recording_bp.route('/testrecording', methods=['GET'])
@handle_errors
@with_vibrationview
def test_recording_connection(vv_instance):
    """
    Test Recording Methods (Diagnostic Endpoint)
    
    Tests recording-related VibrationVIEW methods for connectivity and availability.
    """
    results = {
        'recording_methods': {},
        'system_info': {}
    }
    
    # Test recording methods availability
    try:
        # Test if recording methods are available (may throw if not supported)
        filename = vv_instance.RecordGetFilename()
        
        results['recording_methods'] = {
            'RecordGetFilename_available': True,
            'last_filename': filename
        }
        
    except Exception as e:
        results['recording_methods']['error'] = str(e)
    
    # System info
    try:
        import sys
        import threading
        results['system_info'] = {
            'python_version': sys.version,
            'thread_id': threading.get_ident(),
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        results['system_info']['error'] = str(e)
    
    return jsonify(success_response(
        results,
        "Recording connection diagnostic completed"
    ))