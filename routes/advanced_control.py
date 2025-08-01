# ============================================================================
# FILE: routes/advanced_control.py (Test Control Routes) - Updated for URL Parameters
# ============================================================================

"""
Test Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Advanced test control operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
import logging
from datetime import datetime

# Create blueprint
advanced_control_bp = Blueprint('advanced_control', __name__)

logger = logging.getLogger(__name__)

@advanced_control_bp.route('/docs/advanced_control', methods=['GET'])
def get_documentation():
    """Get test control module documentation"""
    docs = {
        'module': 'advanced_control',
        'description': '1:1 mapping of VibrationVIEW COM advanced test control methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'Sweep Control': {
                'POST /sweepup': {
                    'description': 'Sine sweep up',
                    'com_method': 'SweepUp()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                },
                'POST /sweepdown': {
                    'description': 'Sine sweep down',
                    'com_method': 'SweepDown()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                },
                'POST /sweepstepup': {
                    'description': 'Step up to next integer frequency',
                    'com_method': 'SweepStepUp()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                },
                'POST /sweepstepdown': {
                    'description': 'Step down to next integer frequency',
                    'com_method': 'SweepStepDown()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                },
                'POST /sweephold': {
                    'description': 'Hold sweep frequency',
                    'com_method': 'SweepHold()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                },
                'POST /sweepresonancehold': {
                    'description': 'Hold resonance',
                    'com_method': 'SweepResonanceHold()',
                    'parameters': 'None',
                    'returns': 'boolean - Success status from COM method'
                }
            },
            'Parameter Control (Get/Set)': {
                'GET|POST /demandmultiplier': {
                    'description': 'Get/Set demand output multiplier (dB)',
                    'com_method': 'DemandMultiplier() or DemandMultiplier(value)',
                    'parameters': {
                        'value': 'float - Multiplier value in dB (POST URL parameter only)'
                    },
                    'returns': 'float - Current multiplier value',
                    'example': 'POST /api/demandmultiplier?value=6.0'
                },
                'GET|POST /sweepmultiplier': {
                    'description': 'Get/Set sine sweep multiplier (linear)',
                    'com_method': 'SweepMultiplier() or SweepMultiplier(value)',
                    'parameters': {
                        'value': 'float - Multiplier value (POST URL parameter only)'
                    },
                    'returns': 'float - Current multiplier value',
                    'example': 'POST /api/sweepmultiplier?value=1.5'
                },
                'GET|POST /testtype': {
                    'description': 'Get/Set test type',
                    'com_method': 'TestType() or TestType(value)',
                    'parameters': {
                        'value': 'int - Test type value (POST URL parameter only)'
                    },
                    'returns': 'int - Current test type',
                    'example': 'POST /api/testtype?value=1'
                },
                'GET|POST /sinefrequency': {
                    'description': 'Get/Set sine frequency',
                    'com_method': 'SineFrequency() or SineFrequency(value)',
                    'parameters': {
                        'value': 'float - Frequency value (POST URL parameter only)'
                    },
                    'returns': 'float - Current frequency',
                    'example': 'POST /api/sinefrequency?value=100.0'
                },
                'GET|POST /systemcheckfrequency': {
                    'description': 'Get/Set system check frequency',
                    'com_method': 'SystemCheckFrequency() or SystemCheckFrequency(value)',
                    'parameters': {
                        'value': 'float - Frequency value (POST URL parameter only)'
                    },
                    'returns': 'float - Current frequency',
                    'example': 'POST /api/systemcheckfrequency?value=50.0'
                },
                'GET|POST /systemcheckoutputvoltage': {
                    'description': 'Get/Set system check output level',
                    'com_method': 'SystemCheckOutputVoltage() or SystemCheckOutputVoltage(value)',
                    'parameters': {
                        'value': 'float - Voltage value (POST URL parameter only)'
                    },
                    'returns': 'float - Current voltage',
                    'example': 'POST /api/systemcheckoutputvoltage?value=5.0'
                }
            }
        },
        'notes': [
            'GET requests return current parameter value',
            'POST requests with "value" URL parameter set parameter and return new value',
            'Sweep methods work with sine test types',
            'DemandMultiplier units are in dB, others in their respective units',
            'All POST parameter setting uses URL parameters, not JSON body',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

# Sweep Control (unchanged - no parameters)
@advanced_control_bp.route('/sweepup', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_up(vv_instance):
    """
    Sine Sweep Up
    
    COM Method: SweepUp()
    Increases the frequency during a sine sweep test.
    """
    vv_instance.SweepUp()
    result = True
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepUp command {'executed successfully' if result else 'failed'}"
    ))

@advanced_control_bp.route('/sweepdown', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_down(vv_instance):
    """
    Sine Sweep Down
    
    COM Method: SweepDown()
    Decreases the frequency during a sine sweep test.
    """
    vv_instance.SweepDown()
    result = True
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepDown command {'executed successfully' if result else 'failed'}"
    ))

@advanced_control_bp.route('/sweepstepup', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_step_up(vv_instance):
    """
    Sine Sweep Step Up
    
    COM Method: SweepStepUp()
    Steps up to the next integer frequency during a sine sweep.
    """
    vv_instance.SweepStepUp()
    result = True

    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepStepUp command {'executed successfully' if result else 'failed'}"
    ))

@advanced_control_bp.route('/sweepstepdown', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_step_down(vv_instance):
    """
    Sine Sweep Step Down
    
    COM Method: SweepStepDown()
    Steps down to the next integer frequency during a sine sweep.
    """
    vv_instance.SweepStepDown()
    result = True
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepStepDown command {'executed successfully' if result else 'failed'}"
    ))

@advanced_control_bp.route('/sweephold', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_hold(vv_instance):
    """
    Sine Hold Sweep Frequency
    
    COM Method: SweepHold()
    Holds the current sweep frequency during a sine sweep test.
    """
    vv_instance.SweepHold()
    result = True
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepHold command {'executed successfully' if result else 'failed'}"
    ))

@advanced_control_bp.route('/sweepresonancehold', methods=['POST'])
@handle_errors
@with_vibrationview
def sweep_resonance_hold(vv_instance):
    """
    Sine Hold Resonance
    
    COM Method: SweepResonanceHold()
    Holds at the resonance frequency during a sine sweep test.
    """
    vv_instance.SweepResonanceHold()
    result = True
    
    return jsonify(success_response(
        {'result': result, 'executed': True},
        f"SweepResonanceHold command {'executed successfully' if result else 'failed'}"
    ))

# Parameter Control (Get/Set) - Updated to use URL parameters
@advanced_control_bp.route('/demandmultiplier', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def demand_multiplier(vv_instance):
    """
    Get/Set Demand Output Multiplier
    
    COM Method: DemandMultiplier() or DemandMultiplier(value)
    Controls the multiplier for demand output in dB.
    
    GET: Returns current multiplier value
    POST: Sets multiplier value from URL parameter 'value'
    
    Example: POST /api/demandmultiplier?value=6.0
    """
    if request.method == 'GET':
        result = vv_instance.DemandMultiplier()
        return jsonify(success_response(
            {'result': result},
            f"DemandMultiplier retrieved: {result} dB"
        ))
    else:
        value = request.args.get('value', type=float)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.DemandMultiplier(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"DemandMultiplier set to {value} dB, returned: {result} dB"
        ))

@advanced_control_bp.route('/sweepmultiplier', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def sweep_multiplier(vv_instance):
    """
    Get/Set Sine Sweep Multiplier
    
    COM Method: SweepMultiplier() or SweepMultiplier(value)
    Controls the multiplier for sine sweep (linear scale).
    
    GET: Returns current multiplier value
    POST: Sets multiplier value from URL parameter 'value'
    
    Example: POST /api/sweepmultiplier?value=1.5
    """
    if request.method == 'GET':
        result = vv_instance.SweepMultiplier()
        return jsonify(success_response(
            {'result': result},
            f"SweepMultiplier retrieved: {result}"
        ))
    else:
        value = request.args.get('value', type=float)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.SweepMultiplier(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"SweepMultiplier set to {value}, returned: {result}"
        ))

@advanced_control_bp.route('/testtype', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def test_type(vv_instance):
    """
    Get/Set Test Type
    
    COM Method: TestType() or TestType(value)
    Controls the current test type.
    
    GET: Returns current test type
    POST: Sets test type from URL parameter 'value'
    
    Example: POST /api/testtype?value=1
    """
    if request.method == 'GET':
        result = vv_instance.TestType()
        return jsonify(success_response(
            {'result': result},
            f"TestType retrieved: {result}"
        ))
    else:
        value = request.args.get('value', type=int)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.TestType(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"TestType set to {value}, returned: {result}"
        ))

@advanced_control_bp.route('/sinefrequency', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def sine_frequency(vv_instance):
    """
    Get/Set Sine Frequency
    
    COM Method: SineFrequency() or SineFrequency(value)
    Controls the sine test frequency.
    
    GET: Returns current frequency
    POST: Sets frequency from URL parameter 'value'
    
    Example: POST /api/sinefrequency?value=100.0
    """
    if request.method == 'GET':
        result = vv_instance.SineFrequency()
        return jsonify(success_response(
            {'result': result},
            f"SineFrequency retrieved: {result} Hz"
        ))
    else:
        value = request.args.get('value', type=float)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.SineFrequency(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"SineFrequency set to {value} Hz, returned: {result} Hz"
        ))

@advanced_control_bp.route('/systemcheckfrequency', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def system_check_frequency(vv_instance):
    """
    Get/Set System Check Frequency
    
    COM Method: SystemCheckFrequency() or SystemCheckFrequency(value)
    Controls the system check frequency.
    
    GET: Returns current frequency
    POST: Sets frequency from URL parameter 'value'
    
    Example: POST /api/systemcheckfrequency?value=50.0
    """
    if request.method == 'GET':
        result = vv_instance.SystemCheckFrequency()
        return jsonify(success_response(
            {'result': result},
            f"SystemCheckFrequency retrieved: {result} Hz"
        ))
    else:
        value = request.args.get('value', type=float)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.SystemCheckFrequency(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"SystemCheckFrequency set to {value} Hz, returned: {result} Hz"
        ))

@advanced_control_bp.route('/systemcheckoutputvoltage', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def system_check_output_voltage(vv_instance):
    """
    Get/Set System Check Output Voltage
    
    COM Method: SystemCheckOutputVoltage() or SystemCheckOutputVoltage(value)
    Controls the system check output level.
    
    GET: Returns current voltage
    POST: Sets voltage from URL parameter 'value'
    
    Example: POST /api/systemcheckoutputvoltage?value=5.0
    """
    if request.method == 'GET':
        result = vv_instance.SystemCheckOutputVoltage()
        return jsonify(success_response(
            {'result': result},
            f"SystemCheckOutputVoltage retrieved: {result} V"
        ))
    else:
        value = request.args.get('value', type=float)
        if value is None:
            return jsonify(error_response(
                'Missing required URL parameter: value',
                'MISSING_PARAMETER'
            )), 400
        
        result = vv_instance.SystemCheckOutputVoltage(value)
        return jsonify(success_response(
            {'result': result, 'value_set': value},
            f"SystemCheckOutputVoltage set to {value} V, returned: {result} V"
        ))