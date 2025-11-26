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
                'examples': ['GET /api/v1/reportfield?field=TestName', 'GET /api/v1/reportfield?TestName=']
            },
            'GET|POST /reportfields': {
                'description': 'Get multiple report field values in one call',
                'com_method': 'ReportFields(fields)',
                'parameters': {
                    'fields': 'string or array - Comma-delimited field names or array of field names. Use *| suffix for all channels wildcard. For GET, if only one parameter is provided, it is assumed to be the fields value.'
                },
                'returns': 'array - Report field values in the same order as requested fields',
                'examples': [
                    'GET /api/v1/reportfields?fields=TestName,StartTime,Duration',
                    'GET /api/v1/reportfields?TestName,StartTime,Duration (single param assumed as fields)',
                    'GET /api/v1/reportfields?ChAccelRMS*|,ChDisplacement*|',
                    'POST /api/v1/reportfields with body: {"fields": "TestName,StartTime,Duration"}',
                    'POST /api/v1/reportfields with body: {"fields": ["TestName", "StartTime"]}',
                    'POST /api/v1/reportfields with body: {"fields": "ChAccelRMS*|,ChDisplacement*|"}'
                ]
            },
            'GET /reportvector': {
                'description': 'Get report vector data',
                'com_method': 'ReportVector(vectors, array_out)',
                'parameters': {
                    'vectors': 'str - Vector names to retrieve'
                },
                'returns': 'list - Vector data',
                'example': 'GET /api/v1/reportvector?vectors=Frequency'
            },
            'GET /reportvectorheader': {
                'description': 'Get report vector header information',
                'com_method': 'ReportVectorHeader(vectors, array_out)',
                'parameters': {
                    'vectors': 'str - Vector names to retrieve headers for'
                },
                'returns': 'list - Vector header data',
                'example': 'GET /api/v1/reportvectorheader?vectors=Frequency'
            }
        },
        'notes': [
            'ReportField returns string values for specified report fields',
            'ReportFields accepts comma-delimited field names and returns array of values',
            'ReportFields returns values in the same order as the requested fields',
            'ReportFields supports both GET and POST methods',
            'GET with single parameter assumes that parameter is the fields value',
            'Use *| wildcard suffix to get values for all channels (e.g., "ChAccelRMS*|")',
            'Field names are case-sensitive and must match VibrationVIEW report fields',
            'If COM method raises exception, it will be caught and returned as error',
            'Available report fields depend on the current test and VibrationVIEW configuration',
            'POST accepts both string (comma-delimited) and array formats for fields'
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
        GET /api/v1/reportfield?field=TestName
        GET /api/v1/reportfield?TestName
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

@reporting_bp.route('/reportfields', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def report_fields(vv_instance):
    """
    Get Multiple Report Field Values

    COM Method: ReportFields(fields)
    Gets multiple report values specified by field names in one call.

    GET Query Parameters:
        fields: Comma-delimited field names (e.g., ?fields=TestName,StartTime)
        OR use any parameter name if it's the only parameter (e.g., ?TestName,StartTime)

    POST JSON Body:
        fields: String or array of report field names
                - String: Comma-delimited field names (e.g., "TestName,StartTime,Duration")
                - Array: Will be joined with commas automatically

    Wildcard Support:
        Use *| suffix to get values for all channels
        Example: "ChAccelRMS*|" returns all channel accelerometer RMS values

    Returns:
        results: Array of values corresponding to the requested fields
        fields_string: The comma-delimited string sent to COM

    Examples:
        GET /api/v1/reportfields?fields=TestName,StartTime,Duration
        GET /api/v1/reportfields?TestName,StartTime,Duration
        GET /api/v1/reportfields?ChAccelRMS*|,ChDisplacement*|

        POST /api/v1/reportfields
        Body: {"fields": "TestName,StartTime,Duration"}

        POST /api/v1/reportfields
        Body: {"fields": ["TestName", "StartTime", "Duration"]}

        POST /api/v1/reportfields
        Body: {"fields": "ChAccelRMS*|,ChDisplacement*|"}
    """
    fields = None

    # Handle GET request
    if request.method == 'GET':
        # Try to get 'fields' parameter
        fields = request.args.get('fields')

        # If no 'fields' parameter, use the first query parameter
        if not fields and request.args:
            # Get the first query parameter key as the fields value
            fields = list(request.args.keys())[0]

    # Handle POST request
    else:
        data = request.get_json()
        if data and 'fields' in data:
            fields = data['fields']

    # Validate we have fields
    if not fields:
        return jsonify(error_response(
            'Missing required parameter: fields',
            'MISSING_PARAMETER'
        )), 400

    # Accept both string and array formats
    if isinstance(fields, list):
        if not fields:
            return jsonify(error_response(
                'Parameter "fields" cannot be empty',
                'EMPTY_PARAMETER'
            )), 400
        # Join array with commas
        fields_string = ','.join(fields)
    elif isinstance(fields, str):
        if not fields.strip():
            return jsonify(error_response(
                'Parameter "fields" cannot be empty',
                'EMPTY_PARAMETER'
            )), 400
        fields_string = fields
    else:
        return jsonify(error_response(
            'Parameter "fields" must be a string or array',
            'INVALID_PARAMETER_TYPE'
        )), 400

    # Call ReportFields with the comma-delimited string
    results = vv_instance.ReportFields(fields_string)

    # Convert results to list for JSON serialization and parse delimited data
    results_list = []
    if results is not None:
        for item in results:
            if isinstance(item, (list, tuple)):
                # Parse each element in nested lists/tuples
                parsed_item = []
                for elem in item:
                    if isinstance(elem, str) and ('\t' in elem or '\r\n' in elem):
                        # Split by newline to get rows, remove single trailing tab from each row
                        rows = [(row[:-1] if row.endswith('\t') else row).split('\t') for row in elem.split('\r\n') if row]
                        parsed_item.append(rows)
                    else:
                        parsed_item.append(elem)
                results_list.append(parsed_item)
            elif isinstance(item, str) and ('\t' in item or '\r\n' in item):
                # Split by newline to get rows, remove single trailing tab from each row
                rows = [(row[:-1] if row.endswith('\t') else row).split('\t') for row in item.split('\r\n') if row]
                results_list.append(rows)
            else:
                results_list.append(item)

    response_data = {
        'results': results_list,
        'fields_string': fields_string,
        'executed': True
    }

    message = f"ReportFields executed successfully"

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

    Example: GET /api/v1/reportvector?vectors=Frequency
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

    Example: GET /api/v1/reportvectorheader?vectors=Frequency
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