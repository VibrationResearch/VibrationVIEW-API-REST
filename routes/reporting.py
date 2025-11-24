# ============================================================================
# FILE: routes/reporting.py (Reporting Control Routes) - New Module
# ============================================================================

"""
Reporting Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Report data retrieval operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import extract_com_error_info

import logging
from datetime import datetime

# Create blueprint
reporting_bp = Blueprint('reporting', __name__)

logger = logging.getLogger(__name__)

@reporting_bp.route('/docs/reporting', methods=['GET'])
def get_documentation():
    """Get reporting control module documentation"""
    docs = {
        'module': 'reporting',
        'description': '1:1 mapping of VibrationVIEW COM reporting methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'GET /reportfield': {
                'description': 'Get report value specified by field name',
                'com_method': 'ReportField(sField)',
                'parameters': {
                    'field': 'string - Query parameter with report field name (optional - if missing, uses first query parameter)'
                },
                'returns': 'string - Report field value',
                'examples': ['GET /api/reportfield?field=TestName', 'GET /api/reportfield?TestName=']
            },
            'POST /reportfields': {
                'description': 'Get multiple report field values in one call',
                'com_method': 'Multiple ReportField(sField) calls',
                'parameters': {
                    'fields': 'array - JSON body with array of report field names'
                },
                'returns': 'dict - Report field values with success/error status for each field',
                'example': 'POST /api/reportfields with body: {"fields": ["TestName", "StartTime", "Duration"]}'
            },
            'GET /reportvector': {
                'description': 'Get report vector data',
                'com_method': 'ReportVector(vectors, array_out)',
                'parameters': {
                    'vectors': 'str - Vector names to retrieve'
                },
                'returns': 'list - Vector data',
                'example': 'GET /api/reportvector?vectors=Frequency'
            },
            'GET /reportvectorheader': {
                'description': 'Get report vector header information',
                'com_method': 'ReportVectorHeader(vectors, array_out)',
                'parameters': {
                    'vectors': 'str - Vector names to retrieve headers for'
                },
                'returns': 'list - Vector header data',
                'example': 'GET /api/reportvectorheader?vectors=Frequency'
            }
        },
        'notes': [
            'ReportField returns string values for specified report fields',
            'Field names are case-sensitive and must match VibrationVIEW report fields',
            'If COM method raises exception, it will be caught and returned as error',
            'Available report fields depend on the current test and VibrationVIEW configuration',
            'POST /reportfields allows bulk retrieval with individual error handling per field',
            'Single field errors in bulk requests do not fail the entire operation',
            'COM interface uses 0-based indexing for all arrays'
        ]
    }
    return jsonify(docs)

@reporting_bp.route('/reportfield', methods=['GET'])
@handle_errors
@with_vibrationview
def report_field(vv_instance):
    """
    Get Report Field Value
    
    COM Method: ReportField(sField)
    Gets the report value specified by the field name.
    
    Query Parameters:
        field: Report field name to retrieve (optional - if missing, uses first query parameter)
    
    Examples: 
        GET /api/reportfield?field=TestName
        GET /api/reportfield?TestName
    """
    # Get field name from query string, use first parameter if 'field' is missing
    field_name = request.args.get('field')
    
    if not field_name:
        # Use the first query parameter if 'field' is missing
        if request.args:
            field_name = list(request.args.keys())[0]
        
        if not field_name:
            return jsonify(error_response(
                'Missing query parameter: either "field" or provide any query parameter',
                'MISSING_PARAMETER'
            )), 400
    
    result = vv_instance.ReportField(field_name)
    
    return jsonify(success_response(
        {
            'result': result,
            'field': field_name,
            'executed': True
        },
        f"ReportField executed successfully for field: {field_name}"
    ))

@reporting_bp.route('/reportfields', methods=['POST'])
@handle_errors
@with_vibrationview
def report_fields(vv_instance):
    """
    Get Multiple Report Field Values
    
    COM Method: Multiple ReportField(sField) calls
    Gets multiple report values specified by field names in one call.
    
    JSON Body:
        fields: Array of report field names to retrieve
        channel: Optional integer or "all" - Channel number(s) to append to field names
        loop: Optional integer or "all" - Loop number(s) to append to field names
    
    URL Parameters (alternative to JSON body):
        channel: Optional integer or "all" - Channel number(s) to append to field names
        loop: Optional integer or "all" - Loop number(s) to append to field names
    
    Note: URL parameters take precedence over JSON body parameters
    
    Special Values:
        - channel="all": Gets field for all available input channels
        - loop="all": Gets field for all available output loops
        - Both "all": Gets field for all channel/loop combinations
    
    COM Field Name Format (1-based indexing):
        - Basic: "FieldName" 
        - With channel: "FieldName{channel}:{loop}"
        - Channel only: "FieldName{channel}:"
        - Loop only: "FieldName:{loop}"
        - Channels and loops are 1-based (1, 2, 3, ...)
    
    Results Format:
        - Basic: "FieldName": "value"
        - With channel/loop: "FieldName": {"value": "raw_value", "channel": X, "loop": Y}
        - Multiple: "FieldName": [{"value": "raw_value", "channel": X}, ...]
    
    Examples: 
        POST /api/reportfields
        Body: {"fields": ["MaxLevel"], "channel": "all"}
        
        POST /api/reportfields?channel=all&loop=all
        Body: {"fields": ["MaxLevel"]}
    """
    data = request.get_json()
    
    if not data or 'fields' not in data:
        return jsonify(error_response(
            'Missing required JSON parameter: fields',
            'MISSING_PARAMETER'
        )), 400
    
    fields = data['fields']
    
    # Get channel and loop from URL parameters first (takes precedence), then JSON body
    channel_param = request.args.get('channel') or data.get('channel')
    loop_param = request.args.get('loop') or data.get('loop')
    
    if not isinstance(fields, list):
        return jsonify(error_response(
            'Parameter "fields" must be an array',
            'INVALID_PARAMETER_TYPE'
        )), 400
    
    if not fields:
        return jsonify(error_response(
            'Parameter "fields" cannot be empty',
            'EMPTY_PARAMETER'
        )), 400
    
    # Parse and validate channel parameter
    channels = []
    if channel_param is not None:
        if channel_param == "all":
            try:
                num_channels = vv_instance.GetHardwareInputChannels()
                # Convert to 1-based indexing for COM
                channels = list(range(1, num_channels + 1))
            except Exception as e:
                return jsonify(error_response(
                    f'Failed to get hardware input channels: {str(e)}',
                    'HARDWARE_ERROR'
                )), 500
        else:
            try:
                channel_int = int(channel_param)
                channels = [channel_int]
            except (ValueError, TypeError):
                return jsonify(error_response(
                    'Parameter "channel" must be an integer or "all"',
                    'INVALID_PARAMETER_TYPE'
                )), 400
    
    # Parse and validate loop parameter
    loops = []
    if loop_param is not None:
        if loop_param == "all":
            try:
                num_loops = vv_instance.GetHardwareOutputChannels()
                # Convert to 1-based indexing for COM
                loops = list(range(1, num_loops + 1))
            except Exception as e:
                return jsonify(error_response(
                    f'Failed to get hardware output channels: {str(e)}',
                    'HARDWARE_ERROR'
                )), 500
        else:
            try:
                loop_int = int(loop_param)
                loops = [loop_int]
            except (ValueError, TypeError):
                return jsonify(error_response(
                    'Parameter "loop" must be an integer or "all"',
                    'INVALID_PARAMETER_TYPE'
                )), 400
    
    # Build field names with channel:loop combinations using COM syntax (1-based)
    def build_field_combinations(base_field):
        combinations = []
        
        if not channels and not loops:
            # No channel or loop specified
            combinations.append((base_field, base_field, None, None))
        elif channels and not loops:
            # Channel(s) only - format: "FieldName{channel}:" (1-based)
            for ch in channels:
                com_field_name = f"{base_field}{ch}:"
                combinations.append((base_field, com_field_name, ch, None))
        elif loops and not channels:
            # Loop(s) only - format: "FieldName:{loop}" (1-based)
            for lp in loops:
                com_field_name = f"{base_field}:{lp}"
                combinations.append((base_field, com_field_name, None, lp))
        else:
            # Both channels and loops - format: "FieldName{channel}:{loop}" (1-based)
            for ch in channels:
                for lp in loops:
                    com_field_name = f"{base_field}{ch}:{lp}"
                    combinations.append((base_field, com_field_name, ch, lp))
        
        return combinations
    
    # Format result object with separated channel/loop info
    def format_result(raw_value, channel_num, loop_num):
        if channel_num is None and loop_num is None:
            # No channel/loop info - return raw value
            return raw_value
        
        # Create result object with separated components
        result_obj = {"value": raw_value}
        
        if channel_num is not None:
            result_obj["channel"] = channel_num
        if loop_num is not None:
            result_obj["loop"] = loop_num
            
        return result_obj
    
    # Get all field values
    results = {}
    errors = {}
    
    for field in fields:
        combinations = build_field_combinations(field)
        
        # For single field with multiple combinations, collect all values
        if len(combinations) == 1:
            # Single combination - use field name as key
            result_key, com_field_name, ch, lp = combinations[0]
            try:
                raw_value = vv_instance.ReportField(com_field_name)
                results[result_key] = format_result(raw_value, ch, lp)
            except Exception as e:
                errors[result_key] = str(e)
        else:
            # Multiple combinations - collect into array
            field_values = []
            field_errors = []
            
            for result_key, com_field_name, ch, lp in combinations:
                try:
                    raw_value = vv_instance.ReportField(com_field_name)
                    formatted_result = format_result(raw_value, ch, lp)
                    field_values.append(formatted_result)
                except Exception as e:
                    field_errors.append(f"Error for {com_field_name}: {str(e)}")
            
            if field_values:
                results[field] = field_values
            if field_errors:
                errors[field] = field_errors
    
    # Calculate totals
    total_combinations = sum(len(build_field_combinations(field)) for field in fields)
    
    response_data = {
        'results': results,
        'errors': errors,
        'parameters': {
            'channel': channel_param,
            'loop': loop_param,
            'resolved_channels': channels if channels else None,
            'resolved_loops': loops if loops else None,
            'channel_source': 'url' if request.args.get('channel') else 'json' if channel_param is not None else None,
            'loop_source': 'url' if request.args.get('loop') else 'json' if loop_param is not None else None
        },
        'summary': {
            'requested_fields': len(fields),
            'total_combinations': total_combinations,
            'successful_count': len([v for v in results.values() if v is not None]),
            'error_count': len([v for v in errors.values() if v])
        },
        'executed': True
    }
    
    # Build descriptive message
    successful_results = len([v for v in results.values() if v is not None])
    total_errors = len([v for v in errors.values() if v])
    
    if total_errors:
        message = f"ReportFields executed with {successful_results} successes and {total_errors} errors"
    else:
        message = f"ReportFields executed successfully for {total_combinations} field combinations"
    
    # Add parameter info to message
    param_info = []
    if channel_param == "all":
        param_info.append(f"all {len(channels)} channels")
    elif channel_param is not None:
        param_info.append(f"channel={channel_param}")
    
    if loop_param == "all":
        param_info.append(f"all {len(loops)} loops")
    elif loop_param is not None:
        param_info.append(f"loop={loop_param}")
    
    if param_info:
        message += f" (with {', '.join(param_info)})"
    
    return jsonify(success_response(response_data, message))

@reporting_bp.route('/reportvector', methods=['GET'])
@handle_errors
@with_vibrationview
def report_vector(vv_instance):
    """
    Get Report Vector Data

    COM Method: ReportVector(vectors, array_out)
    Retrieves vector data from the report system.

    Query Parameters:
        vectors: Vector names to retrieve (named parameter)

    Example: GET /api/reportvector?vectors=Frequency
    """
    vectors = request.args.get('vectors')
    if not vectors:
        return jsonify(error_response(
            'Missing required query parameter: vectors',
            'MISSING_PARAMETER'
        )), 400

    result = vv_instance.ReportVector(vectors)

    return jsonify(success_response(
        {'result': result, 'vectors': vectors},
        f"ReportVector executed for: {vectors}"
    ))


@reporting_bp.route('/reportvectorheader', methods=['GET'])
@handle_errors
@with_vibrationview
def report_vector_header(vv_instance):
    """
    Get Report Vector Header Information

    COM Method: ReportVectorHeader(vectors, array_out)
    Retrieves vector header information from the report system.

    Query Parameters:
        vectors: Vector names to retrieve headers for (named parameter)

    Example: GET /api/reportvectorheader?vectors=Frequency
    """
    vectors = request.args.get('vectors')
    if not vectors:
        return jsonify(error_response(
            'Missing required query parameter: vectors',
            'MISSING_PARAMETER'
        )), 400

    result = vv_instance.ReportVectorHeader(vectors)

    return jsonify(success_response(
        {'result': result, 'vectors': vectors},
        f"ReportVectorHeader executed for: {vectors}"
    ))


@reporting_bp.route('/testreporting', methods=['GET'])
@handle_errors
@with_vibrationview
def test_reporting_connection(vv_instance):
    """
    Test Reporting Methods (Diagnostic Endpoint)
    
    Tests reporting-related VibrationVIEW methods for connectivity and availability.
    """
    results = {
        'reporting_methods': {},
        'system_info': {}
    }
    
    # Test reporting methods availability
    try:
        # Test with a common report field (you may need to adjust based on available fields)
        test_field = "TestName"  # Common field that usually exists
        test_result = vv_instance.ReportField(test_field)
        
        results['reporting_methods'] = {
            'ReportField_available': True,
            'test_field': test_field,
            'test_result': test_result
        }
        
    except Exception as e:
        results['reporting_methods']['error'] = str(e)
    
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
        "Reporting connection diagnostic completed"
    ))