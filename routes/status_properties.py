# ============================================================================
# FILE: routes/status_properties.py (Status Properties Routes)
# ============================================================================

"""
Status Properties Routes - 1:1 VibrationVIEW COM Interface Mapping
System status checking and monitoring operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging
import time
from datetime import datetime

# Create blueprint
status_properties_bp = Blueprint('status_properties', __name__)

logger = logging.getLogger(__name__)

@status_properties_bp.route('/docs/status_properties', methods=['GET'])
def get_documentation():
    """Get status properties module documentation"""
    docs = {
        'module': 'status_properties',
        'description': '1:1 mapping of VibrationVIEW COM status and properties methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'GET /status': {
                'description': 'Get comprehensive VibrationVIEW status information',
                'com_method': 'Status()',
                'parameters': 'None',
                'returns': 'dict - Status information with stop_code and stop_code_index'
            },
            'GET /isready': {
                'description': 'Check if VibrationVIEW Ethernet Box is running and ready',
                'com_method': 'IsReady()',
                'parameters': 'None',
                'returns': 'boolean - True if hardware is connected and ready'
            },
            'GET /isrunning': {
                'description': 'Check if a test is currently running',
                'com_method': 'IsRunning()',
                'parameters': 'None',
                'returns': 'boolean - True if test is actively running'
            },
            'GET /isstarting': {
                'description': 'Check if test is starting but not yet at level',
                'com_method': 'IsStarting()',
                'parameters': 'None',
                'returns': 'boolean - True during test startup phase'
            },
            'GET /ischanginglevel': {
                'description': 'Check if test schedule is changing levels',
                'com_method': 'IsChangingLevel()',
                'parameters': 'None',
                'returns': 'boolean - True when transitioning between test levels'
            },
            'GET /isholdlevel': {
                'description': 'Check if schedule timer is in hold state',
                'com_method': 'IsHoldLevel()',
                'parameters': 'None',
                'returns': 'boolean - True when test is paused/held'
            },
            'GET /isopenloop': {
                'description': 'Check if test is running in open loop mode',
                'com_method': 'IsOpenLoop()',
                'parameters': 'None',
                'returns': 'boolean - True if control loop is open'
            },
            'GET /isaborted': {
                'description': 'Check if test has been aborted',
                'com_method': 'IsAborted()',
                'parameters': 'None',
                'returns': 'boolean - True if test was aborted'
            },
            'GET /canresumetest': {
                'description': 'Check if current test can be resumed',
                'com_method': 'CanResumeTest()',
                'parameters': 'None',
                'returns': 'boolean - True if test is resumable'
            },
        },
        'notes': [
            'All methods return actual COM interface values',
            'Boolean methods return True/False based on current system state',
            'Status() returns dictionary with detailed stop information',
            'These are read-only status checking operations',
            'No parameters required for any status endpoints'
        ]
    }
    return jsonify(docs)

# ============================================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================================

@status_properties_bp.route('/status', methods=['GET'])
@handle_errors
@with_vibrationview
def status(vv_instance):
    """
    Get VibrationVIEW Status
    
    COM Method: Status()
    Returns comprehensive status information including stop codes and system state.
    """
    result = vv_instance.Status()
    
    return jsonify(success_response(
        {'result': result},
        "VibrationVIEW status retrieved successfully"
    ))

@status_properties_bp.route('/isready', methods=['GET'])
@handle_errors
@with_vibrationview
def is_ready(vv_instance):
    """
    Check if Ethernet Box is running
    
    COM Method: IsReady()
    Primary health check for VibrationVIEW hardware.
    """
    result = vv_instance.IsReady()
    
    return jsonify(success_response(
        {'result': result},
        f"VibrationVIEW hardware is {'ready' if result else 'not ready'}"
    ))

# ============================================================================
# TEST EXECUTION STATE ENDPOINTS
# ============================================================================

@status_properties_bp.route('/isrunning', methods=['GET'])
@handle_errors
@with_vibrationview
def is_running(vv_instance):
    """
    Check if test is running
    
    COM Method: IsRunning()
    Primary method for monitoring test execution.
    """
    result = vv_instance.IsRunning()
    
    return jsonify(success_response(
        {'result': result},
        f"Test is {'running' if result else 'not running'}"
    ))

@status_properties_bp.route('/isstarting', methods=['GET'])
@handle_errors
@with_vibrationview
def is_starting(vv_instance):
    """
    Check if test is starting but not at level
    
    COM Method: IsStarting()
    Returns True during test initialization phase.
    """
    result = vv_instance.IsStarting()
    
    return jsonify(success_response(
        {'result': result},
        f"Test is {'starting' if result else 'not in startup phase'}"
    ))

@status_properties_bp.route('/ischanginglevel', methods=['GET'])
@handle_errors
@with_vibrationview
def is_changing_level(vv_instance):
    """
    Check if test schedule is changing levels
    
    COM Method: IsChangingLevel()
    Returns True when transitioning between different levels.
    """
    result = vv_instance.IsChangingLevel()
    
    return jsonify(success_response(
        {'result': result},
        f"Test is {'changing levels' if result else 'not changing levels'}"
    ))

@status_properties_bp.route('/isholdlevel', methods=['GET'])
@handle_errors
@with_vibrationview
def is_hold_level(vv_instance):
    """
    Check if schedule timer is in hold
    
    COM Method: IsHoldLevel()
    Returns True when test schedule is paused or held.
    """
    result = vv_instance.IsHoldLevel()
    
    return jsonify(success_response(
        {'result': result},
        f"Test is {'on hold' if result else 'not on hold'}"
    ))

# ============================================================================
# TEST CONTROL STATE ENDPOINTS
# ============================================================================

@status_properties_bp.route('/isopenloop', methods=['GET'])
@handle_errors
@with_vibrationview
def is_open_loop(vv_instance):
    """
    Check if test is open loop
    
    COM Method: IsOpenLoop()
    Returns True when control system has lost feedback.
    """
    result = vv_instance.IsOpenLoop()
    
    return jsonify(success_response(
        {'result': result},
        f"Test is {'in open loop mode' if result else 'in closed loop mode'}"
    ))

@status_properties_bp.route('/isaborted', methods=['GET'])
@handle_errors
@with_vibrationview
def is_aborted(vv_instance):
    """
    Check if test has aborted
    
    COM Method: IsAborted()
    Returns True when test has been aborted due to error or user action.
    """
    result = vv_instance.IsAborted()
    
    return jsonify(success_response(
        {'result': result},
        f"Test {'has been aborted' if result else 'has not been aborted'}"
    ))

# ============================================================================
# RESUME CAPABILITIES ENDPOINTS
# ============================================================================

@status_properties_bp.route('/canresumetest', methods=['GET'])
@handle_errors
@with_vibrationview
def can_resume_test(vv_instance):
    """
    Check if test may be resumed
    
    COM Method: CanResumeTest()
    Returns True if current test can be resumed from stopped state.
    """
    result = vv_instance.CanResumeTest()
    
    return jsonify(success_response(
        {'result': result},
        f"Test {'can be resumed' if result else 'cannot be resumed'}"
    ))
@handle_errors

@status_properties_bp.route('/allstatus', methods=['GET'])
@handle_errors
@with_vibrationview
def test_com_connection(vv_instance):
    """
    Test COM Connection (Diagnostic Endpoint)
    
    Tests status properties COM connection and capabilities.
    """
    results = {
        'connection': {'success': False, 'error': None},
        'status_tests': {}
    }
    
    # Test status properties connection
    try:
        # Test basic status methods
        results['status_tests'] = {
                'is_ready': vv_instance.IsReady(),
                'is_running': vv_instance.IsRunning(),
                'is_starting': vv_instance.IsStarting(),
                'is_changing_level': vv_instance.IsChangingLevel(),
                'is_hold_level': vv_instance.IsHoldLevel(),
                'is_open_loop': vv_instance.IsOpenLoop(),
                'is_aborted': vv_instance.IsAborted(),
                'can_resume_test': vv_instance.CanResumeTest(),
                'status': vv_instance.Status()
        }
        
        results['connection'] = {
            'success': True,
            'tests_completed': len(results['status_tests'])
        }
    except Exception as e:
        results['connection']['error'] = str(e)
    
    return jsonify(success_response(
        results,
        "Status properties COM connection diagnostic completed"
    ))

