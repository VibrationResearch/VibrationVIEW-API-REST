# ============================================================================
# GUI Control Routes 
# ============================================================================

"""
GUI Control Routes - 1:1 VibrationVIEW COM Interface Mapping
GUI and window management operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging
from datetime import datetime

# Create blueprint
gui_control_bp = Blueprint('gui_control', __name__)

logger = logging.getLogger(__name__)

@gui_control_bp.route('/docs/gui_control', methods=['GET'])
def get_documentation():
    """Get GUI control module documentation"""
    docs = {
        'module': 'gui_control',
        'description': '1:1 mapping of VibrationVIEW COM GUI control methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Test Editing': {
                'GET /edittest': {
                    'description': 'Edit VibrationVIEW Test',
                    'com_method': 'EditTest(szTestName)',
                    'parameters': {
                        'testname': 'string - Test name to edit'
                    },
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /abortedit': {
                    'description': 'Abort any open Edit session',
                    'com_method': 'AbortEdit()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                }
            },
            'Window Management': {
                'GET /minimize': {
                    'description': 'Minimize VibrationVIEW',
                    'com_method': 'Minimize()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /restore': {
                    'description': 'Restore VibrationVIEW',
                    'com_method': 'Restore()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /maximize': {
                    'description': 'Maximize VibrationVIEW',
                    'com_method': 'Maximize()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                },
                'GET /activate': {
                    'description': 'Activate VibrationVIEW',
                    'com_method': 'Activate()',
                    'parameters': 'None',
                    'returns': 'HRESULT - Success status from COM method'
                }
            }
        },
        'notes': [
            'GET requests with parameters use URL query strings',
            'All methods return HRESULT status codes',
            'EditTest requires valid test file name',
            'Window management methods affect VibrationVIEW main window',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

# Test Editing Control
@gui_control_bp.route('/edittest', methods=['GET'])
@handle_errors
@with_vibrationview
def edit_test(vv_instance):
    """
    Edit VibrationVIEW Test
    
    COM Method: EditTest(szTestName)
    Opens the specified test for editing in VibrationVIEW.
    """
    test_name = request.args.get('testname', type=str)
    if test_name is None:
        return jsonify(error_response(
            'Missing required parameter: testname',
            'MISSING_PARAMETER'
        )), 400
    
    result = vv_instance.EditTest(test_name)
    
    return jsonify(success_response(
        {'result': result, 'test_name': test_name, 'executed': True},
        f"EditTest command executed for '{test_name}' - Result: {result}"
    ))

@gui_control_bp.route('/abortedit', methods=['GET'])
@handle_errors
@with_vibrationview
def abort_edit(vv_instance):
    """
    Abort Edit Session
    
    COM Method: AbortEdit()
    Aborts any currently open edit session without saving changes.
    """
    result = vv_instance.AbortEdit()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"AbortEdit command executed - Result: {result}"
    ))

# Window Management Control
@gui_control_bp.route('/minimize', methods=['GET'])
@handle_errors
@with_vibrationview
def minimize(vv_instance):
    """
    Minimize VibrationVIEW
    
    COM Method: Minimize()
    Minimizes the VibrationVIEW application window.
    """
    result = vv_instance.Minimize()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Minimize command executed - Result: {result}"
    ))

@gui_control_bp.route('/restore', methods=['GET'])
@handle_errors
@with_vibrationview
def restore(vv_instance):
    """
    Restore VibrationVIEW
    
    COM Method: Restore()
    Restores the VibrationVIEW application window from minimized state.
    """
    result = vv_instance.Restore()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Restore command executed - Result: {result}"
    ))

@gui_control_bp.route('/maximize', methods=['GET'])
@handle_errors
@with_vibrationview
def maximize(vv_instance):
    """
    Maximize VibrationVIEW
    
    COM Method: Maximize()
    Maximizes the VibrationVIEW application window.
    """
    result = vv_instance.Maximize()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Maximize command executed - Result: {result}"
    ))

@gui_control_bp.route('/activate', methods=['GET'])
@handle_errors
@with_vibrationview
def activate(vv_instance):
    """
    Activate VibrationVIEW
    
    COM Method: Activate()
    Brings the VibrationVIEW application window to the foreground and activates it.
    """
    result = vv_instance.Activate()
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"Activate command executed - Result: {result}"
    ))