# ============================================================================
# FILE: routes/basic_control.py (Basic Control Routes) - v36
# ============================================================================

"""
Basic Control Routes - 1:1 VibrationVIEW COM Interface Mapping
Core test control operations matching exact COM method signatures
"""

from flask import Blueprint, request, jsonify
from urllib.parse import unquote
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response, error_response
from utils.decorators import handle_errors
from utils.utils import handle_binary_upload, extract_com_error_info, is_template_file, get_new_test_defaults_path, is_default_template_filename
from utils.path_validator import validate_file_path, PathValidationError

import logging
import os
from datetime import datetime
import config

# Create blueprint
basic_control_bp = Blueprint('basic_control', __name__)

logger = logging.getLogger(__name__)

# Constants
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB limit

@basic_control_bp.route('/docs/basic_control', methods=['GET'])
def get_documentation():
    """Get basic control module documentation"""
    docs = {
        'module': 'basic_control',
        'description': '1:1 mapping of VibrationVIEW COM basic control methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'GET|POST /starttest': {
                'description': 'Start currently loaded VibrationVIEW test',
                'com_method': 'StartTest()',
                'parameters': 'None',
                'returns': 'Result from StartTest()',
                'example': 'GET /api/v1/starttest or POST /api/v1/starttest'
            },
            'GET|POST /runtest': {
                'description': 'Open and run a complete test (combines OpenTest + StartTest)',
                'com_method': 'RunTest(filepath)',
                'parameters': {
                    'testname': 'string - Query parameter with VibrationVIEW profile filename (named parameter)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter'
                },
                'returns': 'boolean - Test running status verified by IsRunning()',
                'example': 'GET /api/v1/runtest (status) or GET /api/v1/runtest?testname=test1.vsp or POST /api/v1/runtest?testname=test1.vsp'
            },
            'PUT /runtest': {
                'description': 'Upload and run a complete test (combines upload + OpenTest + StartTest)',
                'com_method': 'OpenTest(filepath) + StartTest()',
                'parameters': {
                    'filename': 'string - Query parameter with desired filename (named parameter)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter',
                    'body': 'binary - File content in request body'
                },
                'headers': {
                    'Content-Length': 'required - File size in bytes (max 10MB)'
                },
                'returns': 'object - Status, test running verification, file path, and size information',
                'example': 'PUT /api/v1/runtest?filename=test1.vsp or PUT /api/v1/runtest?test1.vsp (with binary file in body)'
            },
           'GET|POST /stoptest': {
                'description': 'Stop currently running test',
                'com_method': 'StopTest()',
                'parameters': 'None',
                'returns': 'Result from StopTest()',
                'example': 'GET /api/v1/stoptest or POST /api/v1/stoptest'
            },
            'GET|POST /resumetest': {
                'description': 'Resume paused test',
                'com_method': 'ResumeTest()',
                'parameters': 'None',
                'returns': 'Result from ResumeTest()',
                'example': 'GET /api/v1/resumetest or POST /api/v1/resumetest'
            },
            'GET|POST /opentest': {
                'description': 'Open test profile file by filename',
                'com_method': 'OpenTest(filepath)',
                'parameters': {
                    'testname': 'string - Query parameter with VibrationVIEW profile filename (named parameter)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter'
                },
                'returns': 'Result from OpenTest()',
                'example': 'GET /api/v1/opentest?testname=test1.vsp or POST /api/v1/opentest?test1.vsp'
            },
            'PUT /opentest': {
                'description': 'Upload and open test profile file',
                'com_method': 'OpenTest(filepath)',
                'parameters': {
                    'filename': 'string - Query parameter with desired filename (named parameter)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter',
                    'body': 'binary - File content in request body'
                },
                'headers': {
                    'Content-Length': 'required - File size in bytes (max 10MB)'
                },
                'returns': 'object - Status, color, file path, and size information',
                'example': 'PUT /api/v1/opentest?filename=test1.vsp or PUT /api/v1/opentest?test1.vsp (with binary file in body)'
            },
            'GET|POST /closetest': {
                'description': 'Close test profile by name',
                'com_method': 'CloseTest(profile_name)',
                'parameters': {
                    'profilename': 'string - Query parameter with profile name (named parameter)',
                    'OR unnamed parameter': 'string - Profile name as first URL parameter'
                },
                'returns': 'boolean - test_was_closed status',
                'example': 'GET /api/v1/closetest?profilename=test1.vsp or POST /api/v1/closetest?test1.vsp'
            },
            'GET|POST /closetab': {
                'description': 'Close test tab by index',
                'com_method': 'CloseTab(tab_index)',
                'parameters': {
                    'tabindex': 'integer - Query parameter with tab index (0-based, named parameter)',
                    'OR unnamed parameter': 'integer - Tab index as first URL parameter'
                },
                'returns': 'boolean - test_was_closed status (200 on success, 405 if tab could not be closed)',
                'status_codes': {
                    '200': 'Success - tab was closed',
                    '400': 'Missing or invalid tab index parameter',
                    '405': 'Tab could not be closed (may not exist or may be running a test)'
                },
                'example': 'GET /api/v1/closetab?tabindex=0 or POST /api/v1/closetab?tabindex=1 or GET /api/v1/closetab?0'
            },
            'GET /listopentests': {
                'description': 'List all open test profiles with detailed information',
                'com_method': 'ListOpenTests()',
                'parameters': 'None',
                'returns': {
                    'open_tests': '2D array - Each row contains [Tab Index, Test Type, File Path, Test Name]',
                    'columns': 'array - Column headers ["Tab Index", "Test Type", "File Path", "Test Name"]',
                    'count': 'integer - Number of open tests'
                },
                'column_structure': [
                    'Column 0: Tab index (1-based string, e.g., "1", "2", "3")',
                    'Column 1: Test type label (e.g., "Random", "Sine", "Shock")',
                    'Column 2: Full file path of the test profile',
                    'Column 3: Test name (displayed on tabs)'
                ],
                'example': 'GET /api/v1/listopentests'
            },
            'GET|POST /savedata': {
                'description': 'Save current test data to file',
                'com_method': 'SaveData(filename)',
                'parameters': {
                    'filename': 'string - Filename or full path to save data to (named parameter). If only filename is provided, DATA_FOLDER is used as default path.'
                },
                'returns': 'Success status with saved file path',
                'examples': [
                    'POST /api/v1/savedata?filename=savefile.vsd (saves to DATA_FOLDER)',
                    'POST /api/v1/savedata?filename=C:\\Custom\\Path\\savefile.vsd (saves to custom path)'
                ]
            }
        },
        'notes': [
            'All endpoints are 1:1 COM method mappings unless explicitly noted as composite operations',
            'If COM method raises exception, it will be caught and returned as error',
            'StartTest requires a test to be previously loaded with OpenTest',
            'File paths should use full absolute paths',
            'COM interface uses 0-based indexing for all arrays',
            'PUT endpoints accept binary file uploads up to 10MB',
            'All endpoints support both named parameters (e.g., testname=file.vsp) and unnamed parameters (e.g., file.vsp)',
            'Query strings are URL-decoded to handle special characters in filenames',
            'GET and POST methods behave identically for all endpoints that support both'
        ]
    }
    return jsonify(docs)

@basic_control_bp.route('/starttest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def start_test(vv_instance):
    """
    Start Currently Loaded VibrationVIEW Test

    COM Method: StartTest()
    Starts execution of a test that has been previously loaded with
    OpenTest. If no test is loaded, this will fail.
    """
    result = vv_instance.StartTest()

    # Check if test is actually running
    success = vv_instance.IsRunning()

    return jsonify(success_response(
        {'result': result},
        "StartTest command executed"
    ))

@basic_control_bp.route('/runtest', methods=['PUT'])
@handle_errors
@with_vibrationview
def upload_and_run_test(vv_instance):
    """
    Upload and Run Complete Test (Upload + Open + Start)
    
    COM Methods: OpenTest(filepath) + StartTest()
    Uploads a VibrationVIEW profile file, opens it, and starts execution in one operation.
    
    Query Parameters:
        filename: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter
    
    Headers:
        Content-Length: Required - File size in bytes (max 10MB)
    
    Body:
        Binary file content
    
    Example: PUT /api/v1/runtest?filename=test1.vsp or PUT /api/v1/runtest?test1.vsp (with binary file in body)
    """
    # Get filename from parameters - check named parameter first, then unnamed
    filename = request.args.get("filename")

    # If no 'filename' parameter, try to get the first unnamed parameter
    if filename is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters
            filename = unquote(query_string)

    content_length = request.content_length

    if not filename:
        return jsonify({'Error': 'Missing required query parameter: filename (or unnamed filename parameter)'}), 400

    if content_length is None:
        return jsonify({'Error': 'Missing Content-Length header'}), 411  # Length Required

    if content_length > MAX_CONTENT_LENGTH:
        return jsonify({'Error': 'File too large (max 10MB)'}), 413  # Payload Too Large

    binary_data = request.get_data()
    result, error, status_code = handle_binary_upload(filename, binary_data)
    if error:
        return jsonify(error), status_code

    file_path = result['FilePath']

    # Open the uploaded test file
    run_result = vv_instance.RunTest(file_path)

    # Check if test is actually running
    success = vv_instance.IsRunning()

    return jsonify(success_response(
        {
            'result': success,
            'filepath': filename,
            'file_uploaded': True,
            'test_opened': True,
            'test_started': success,
            'executed': True
        },
        f"Upload and RunTest command {'executed successfully' if success else 'failed'}: {filename}"
    ))
    
@basic_control_bp.route('/runtest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def run_test(vv_instance):
    """
    Run Complete Test (Open + Start)

    COM Method: RunTest(filepath)
    Opens a VibrationVIEW profile file and starts execution in one operation.

    Query Parameters:
        testname: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter

    Example: GET /api/v1/runtest?testname=test1.vsp or POST /api/v1/runtest?test1.vsp
    """
    # Get test name from parameters - check named parameter first, then unnamed
    test_name = request.args.get("testname")

    # If no 'testname' parameter, try to get the first unnamed parameter
    if test_name is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters like : and \
            test_name = unquote(query_string)

    if not test_name:
        return jsonify(error_response(
            'Missing required query parameter: testname (or unnamed test filename parameter)',
            'MISSING_PARAMETER'
        )), 400

    # Use test_name as provided
    filepath = test_name

    # Call RunTest method
    result = vv_instance.RunTest(filepath)

    return jsonify(success_response(
        {
            'result': result,
            'filepath': filepath
        },
        f"RunTest command executed: {test_name}"
    ))

@basic_control_bp.route('/stoptest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def stop_test(vv_instance):
    """
    Stop Currently Running Test

    COM Method: StopTest()
    Terminates the currently running vibration test.
    """
    result = vv_instance.StopTest()
    # Check if test actually stopped
    success = not vv_instance.IsRunning()

    return jsonify(success_response(
        {'result': result},
        "StopTest command executed"
    ))

@basic_control_bp.route('/resumetest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def resume_test(vv_instance):
    """
    Resume Paused Test

    COM Method: ResumeTest()
    Resumes a previously paused vibration test.
    """
    result = vv_instance.ResumeTest()

    # Check if test is actually running
    success = vv_instance.IsRunning()

    return jsonify(success_response(
        {'result': result},
        "ResumeTest command executed"
    ))

@basic_control_bp.route('/opentest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def open_test(vv_instance):
    """
    Open Test Profile File by Filename

    COM Method: OpenTest(filepath)
    Opens a VibrationVIEW profile file for execution.
    The test can then be started with StartTest.

    Query Parameters:
        testname: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter

    Example: GET /api/v1/opentest?testname=test1.vsp or POST /api/v1/opentest?test1.vsp
    """
    # Get test name from parameters - check named parameter first, then unnamed
    test_name = request.args.get("testname")

    # If no 'testname' parameter, try to get the first unnamed parameter
    if test_name is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters like : and \
            test_name = unquote(query_string)

    if not test_name:
        return jsonify(error_response(
            'Missing required query parameter: testname (or unnamed test filename parameter)',
            'MISSING_PARAMETER'
        )), 400

    # Use test_name as provided
    filepath = test_name

    result = vv_instance.OpenTest(filepath)

    return jsonify(success_response(
        {
            'result': result,
            'filepath': filepath
        },
        f"OpenTest command executed: {test_name}"
    ))

@basic_control_bp.route('/opentest', methods=['PUT'])
@with_vibrationview
def upload_and_open_test(vv_instance):
    """
    Upload and Open Test Profile File
    
    COM Method: OpenTest(filepath)
    Uploads a VibrationVIEW profile file and opens it for execution.
    The test can then be started with StartTest.
    
    Query Parameters:
        filename: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter
    
    Headers:
        Content-Length: Required - File size in bytes (max 10MB)
    
    Body:
        Binary file content
    
    Example: PUT /api/v1/opentest?filename=test1.vsp or PUT /api/v1/opentest?test1.vsp (with binary file in body)
    """
    try:
        # Get filename from parameters - check named parameter first, then unnamed
        filename = request.args.get("filename")
        
        # If no 'filename' parameter, try to get the first unnamed parameter
        if filename is None:
            query_string = request.query_string.decode('utf-8')
            if query_string:
                # URL decode the query string to handle special characters
                filename = unquote(query_string)
        
        content_length = request.content_length

        if not filename:
            return jsonify({'Error': 'Missing required query parameter: filename (or unnamed filename parameter)'}), 400

        if content_length is None:
            return jsonify({'Error': 'Missing Content-Length header'}), 411  # Length Required
        
        if content_length > MAX_CONTENT_LENGTH:
            return jsonify({'Error': 'File too large (max 10MB)'}), 413  # Payload Too Large
        
        binary_data = request.get_data()
        
        # Check if this is a template file and handle accordingly
        if is_template_file(filename):
            # Get the New Test Defaults path from registry
            defaults_path = get_new_test_defaults_path()
            if defaults_path:
                # Use the New Test Defaults folder for template files
                result, error, status_code = handle_binary_upload(filename, binary_data, uploadsubfolder=defaults_path, usetemporaryfile=False)
            else:
                # Fallback to regular Uploads folder if registry path not found
                result, error, status_code = handle_binary_upload(filename, binary_data)
        else:
            # Regular file handling
            result, error, status_code = handle_binary_upload(filename, binary_data)
        
        if error:
            return jsonify(error), status_code

        file_path = result['FilePath']

        # Check if this is a default template filename that should only be copied
        if is_default_template_filename(filename):
            return jsonify(success_response(
                {
                    'result': True,
                    'filepath': filename,
                    'executed': False,
                    'copied_only': True
                },
                f"Default template file uploaded and copied only (OpenTest automation not run on default filename): {filename}"
            ))

        # close any existing test with the same name to avoid conflicts
        existing_tests = vv_instance.ListOpenTests()
        if existing_tests:
            basename_lower = os.path.splitext(os.path.basename(filename))[0].lower()
            
            for test in existing_tests:
                test_name = test[3].lower() if test[3] else ''
                
                if basename_lower == test_name:
                    vv_instance.CloseTest(int(test[0]))

        # Open the uploaded test file
        result = vv_instance.OpenTest(file_path)

        # Handle None return - assume success if no exception was raised
        success = True  # True if result is None or True
        
        return jsonify(success_response(
            {
                'result': success,
                'filepath': filename,
                'executed': True
            },
            f"OpenTest command {'executed successfully' if success else 'failed'}: {filename}"
        ))

    except Exception as e:
        return jsonify(extract_com_error_info(e)), 500

@basic_control_bp.route('/closetest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def close_test(vv_instance):
    """
    Close Test Profile by Name

    COM Method: CloseTest(profile_name)
    Closes an open VibrationVIEW test profile by its filename.

    Query Parameters:
        profilename: string - Profile name (named parameter)
        OR unnamed parameter: string - Profile name as first URL parameter

    Returns:
        boolean - test_was_closed status indicating whether the test was successfully closed

    Example: GET /api/v1/closetest?profilename=test1.vsp or POST /api/v1/closetest?test1.vsp
    """
    # Get profile name from parameters - check named parameter first, then unnamed
    profile_name = request.args.get("profilename")

    # If no 'profilename' parameter, try to get the first unnamed parameter
    if profile_name is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters
            profile_name = unquote(query_string)

    if not profile_name:
        return jsonify(error_response(
            'Missing required query parameter: profilename (or unnamed profile name parameter)',
            'MISSING_PARAMETER'
        )), 400

    # Call CloseTest method
    test_was_closed = vv_instance.CloseTest(profile_name)

    return jsonify(success_response(
        {
            'test_was_closed': test_was_closed,
            'profile_name': profile_name
        },
        f"CloseTest command executed: {profile_name}"
    ))

@basic_control_bp.route('/closetab', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def close_tab(vv_instance):
    """
    Close Test Tab by Index

    COM Method: CloseTab(tab_index)
    Closes an open VibrationVIEW test tab by its index (0-based).

    Query Parameters:
        tabindex: integer - Tab index (0-based, named parameter)
        OR unnamed parameter: integer - Tab index as first URL parameter

    Returns:
        200: Success - tab was closed successfully
        400: Missing or invalid tab index parameter
        405: Tab could not be closed (may not exist or may be running a test)

    Example: GET /api/v1/closetab?tabindex=0 or POST /api/v1/closetab?tabindex=1
             GET /api/v1/closetab?0 or POST /api/v1/closetab?2 (unnamed parameter)
    """
    # Get tab index from parameters - check named parameter first, then unnamed
    tab_index_str = request.args.get("tabindex")

    # If no 'tabindex' parameter, try to get the first unnamed parameter
    if tab_index_str is None:
        query_string = request.query_string.decode('utf-8')
        if query_string:
            # URL decode the query string to handle special characters
            tab_index_str = unquote(query_string)

    if not tab_index_str:
        return jsonify(error_response(
            'Missing required query parameter: tabindex (or unnamed tab index parameter)',
            'MISSING_PARAMETER'
        )), 400

    try:
        tab_index = int(tab_index_str)
    except ValueError:
        return jsonify(error_response(
            f'Invalid tab index: {tab_index_str}. Must be an integer.',
            'INVALID_PARAMETER'
        )), 400

    # Call CloseTab method
    test_was_closed = vv_instance.CloseTab(tab_index)

    # Return 405 if the tab was not closed
    if not test_was_closed:
        return jsonify(error_response(
            f'Tab {tab_index} could not be closed (may not exist or may be running a test)',
            'TAB_NOT_CLOSED'
        )), 405

    return jsonify(success_response(
        {
            'test_was_closed': test_was_closed,
            'tab_index': tab_index
        },
        f"CloseTab command executed: tab {tab_index}"
    ))

@basic_control_bp.route('/listopentests', methods=['GET'])
@handle_errors
@with_vibrationview
def list_open_tests(vv_instance):
    """
    List All Open Test Profiles

    COM Method: ListOpenTests()
    Returns a 2D array of all currently open VibrationVIEW test profiles.
    Each row contains 4 columns of information about an open test.

    Returns:
        array - List of open test profiles (2D array)
        columns - Column headers describing the data structure
        count - Number of open tests

    Column Structure:
        - Column 0: Tab index (1-based string, e.g., "1", "2", "3")
        - Column 1: Test type label (e.g., "Random", "Sine", "Shock")
        - Column 2: Full file path of the test profile
        - Column 3: Test name (displayed on tabs)

    Example: GET /api/v1/listopentests
    """
    # Call ListOpenTests method
    open_tests = vv_instance.ListOpenTests()

    # Convert to list if it's a tuple or other iterable
    if open_tests is not None:
        open_tests_list = list(open_tests)
    else:
        open_tests_list = []

    # Column headers for the data structure
    column_headers = [
        "Tab Index",       # Column 0: 1-based tab index
        "Test Type",       # Column 1: Test type label (Random, Sine, Shock, etc.)
        "File Path",       # Column 2: Full file path
        "Test Name"        # Column 3: Test name on tab
    ]

    return jsonify(success_response(
        {
            'open_tests': open_tests_list,
            'columns': column_headers,
            'count': len(open_tests_list)
        },
        f"ListOpenTests command executed: {len(open_tests_list)} test(s) open"
    ))

@basic_control_bp.route('/savedata', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def save_data(vv_instance):
    """
    Save Current Test Data

    COM Method: SaveData(filename)
    Saves the current test data to the specified filename.
    If only a filename is provided (no path), DATA_FOLDER is used as the default path.
    Raises VVIEW_E_FAILEDTOSAVE on failure.

    Query Parameters:
        filename: Filename or full path to save data to (named parameter)

    Examples:
        POST /api/v1/savedata?filename=savefile.vsd (saves to DATA_FOLDER/savefile.vsd)
        POST /api/v1/savedata?filename=C:\Custom\Path\savefile.vsd (saves to specified path)
    """
    filename = request.args.get('filename')
    if not filename:
        return jsonify(error_response(
            'Missing required query parameter: filename',
            'MISSING_PARAMETER'
        )), 400

    # If filename has no path separators, prepend DATA_FOLDER
    if not os.path.dirname(filename):
        file_path = os.path.join(config.Config.DATA_FOLDER, filename)
    else:
        file_path = filename

    # Validate file path security
    try:
        validated_file_path = validate_file_path(file_path, "save data")
    except PathValidationError as e:
        return jsonify(error_response(
            str(e),
            'PATH_VALIDATION_ERROR'
        )), 403

    # SaveData has no return value, raises exception on failure
    vv_instance.SaveData(validated_file_path)

    return jsonify(success_response(
        {'filename': filename, 'path': validated_file_path},
        f"Data saved successfully to: {validated_file_path}"
    ))

@basic_control_bp.route('/testcom', methods=['GET'])
@handle_errors
@with_vibrationview
def test_com_connection(vv_instance):
    """
    Test COM Connection (Diagnostic Endpoint)
    
    Tests VibrationVIEW connection using the official thread-safe API.
    """
    results = {
        'connection': {'success': False, 'error': None},
        'system_info': {}
    }
    
    # Test VibrationVIEW connection
    try:
        # Test basic connection
        version = vv_instance.GetSoftwareVersion()
        hardware_inputs = vv_instance.GetHardwareInputChannels()
        hardware_outputs = vv_instance.GetHardwareOutputChannels()
        serial_number = vv_instance.GetHardwareSerialNumber()
        is_ready = vv_instance.IsReady()
        
        results['connection'] = {
            'success': True,
            'version': version,
            'hardware_inputs': hardware_inputs,
            'hardware_outputs': hardware_outputs,
            'serial_number': serial_number,
            'is_ready': is_ready
        }
    except Exception as e:
        results['connection']['error'] = str(e)
    
    # System info
    try:
        import sys
        import threading
        results['system_info'] = {
            'python_version': sys.version,
            'python_architecture': '64-bit' if sys.maxsize > 2**32 else '32-bit',
            'thread_id': threading.get_ident(),
            'vibrationview_api_available': True
        }
    except Exception as e:
        results['system_info']['error'] = str(e)
    
    return jsonify(success_response(
        results,
        "COM connection diagnostic completed"
    ))