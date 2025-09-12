# ============================================================================
# FILE: routes/basic_control.py (Basic Control Routes) - v35
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

import logging
from datetime import datetime

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
            'POST /starttest': {
                'description': 'Start currently loaded VibrationVIEW test',
                'com_method': 'StartTest()',
                'parameters': 'None',
                'returns': 'boolean - Test running status verified by IsRunning()'
            },
            'GET /runtest': {
                'description': 'Get current running test status',
                'com_method': 'IsRunning()',
                'parameters': 'None',
                'returns': 'boolean - Current test running status',
                'example': 'GET /api/runtest'
            },
            'GET|POST /runtest': {
                'description': 'Get test status / Open and run a complete test (combines OpenTest + StartTest)',
                'com_method': 'IsRunning() or RunTest(filepath)',
                'parameters': {
                    'testname': 'string - Query parameter with VibrationVIEW profile filename (named parameter, POST only)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter (POST only)'
                },
                'returns': 'boolean - Test running status verified by IsRunning()',
                'example': 'GET /api/runtest (status) or POST /api/runtest?testname=test1.vsp or POST /api/runtest?test1.vsp'
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
                'example': 'PUT /api/runtest?filename=test1.vsp or PUT /api/runtest?test1.vsp (with binary file in body)'
            },
           'POST /stoptest': {
                'description': 'Stop currently running test',
                'com_method': 'StopTest()',
                'parameters': 'None',
                'returns': 'boolean - Test stopped status verified by IsRunning()'
            },
            'POST /resumetest': {
                'description': 'Resume paused test',
                'com_method': 'ResumeTest()',
                'parameters': 'None',
                'returns': 'boolean - Test running status verified by IsRunning()'
            },
            'GET /opentest': {
                'description': 'Get current test ready status',
                'com_method': 'IsReady()',
                'parameters': 'None',
                'returns': 'boolean - Current test ready status',
                'example': 'GET /api/opentest'
            },
            'GET|POST /opentest': {
                'description': 'Get test ready status / Open test profile file by filename',
                'com_method': 'IsReady() or OpenTest(filepath)',
                'parameters': {
                    'testname': 'string - Query parameter with VibrationVIEW profile filename (named parameter, POST only)',
                    'OR unnamed parameter': 'string - Test filename as first URL parameter (POST only)'
                },
                'returns': 'boolean - Success status from COM method',
                'example': 'GET /api/opentest (status) or POST /api/opentest?testname=test1.vsp or POST /api/opentest?test1.vsp'
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
                'example': 'PUT /api/opentest?filename=test1.vsp or PUT /api/opentest?test1.vsp (with binary file in body)'
            }
        },
        'notes': [
            'Success for start/run/resume operations verified by IsRunning() status',
            'Success for stop operation verified by NOT IsRunning() status',
            'If COM method raises exception, it will be caught and returned as error',
            'StartTest requires a test to be previously loaded with OpenTest',
            'File paths should use full absolute paths',
            'COM interface uses 0-based indexing for all arrays',
            'PUT /opentest accepts binary file uploads up to 10MB',
            'POST /opentest works with existing files by filename',
            'All endpoints support both named parameters (e.g., testname=file.vsp) and unnamed parameters (e.g., file.vsp)',
            'Query strings are URL-decoded to handle special characters in filenames',
            'GET /runtest returns current test running status without parameters',
            'GET /opentest returns current test ready status without parameters',
            'POST /runtest and POST /opentest require testname parameter or unnamed parameter'
        ]
    }
    return jsonify(docs)

@basic_control_bp.route('/starttest', methods=['POST'])
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
        {'result': success, 'executed': True},
        f"StartTest command {'executed successfully' if success else 'failed'}"
    ))

@basic_control_bp.route('/runtest', methods=['PUT'])
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
    
    Example: PUT /api/runtest?filename=test1.vsp or PUT /api/runtest?test1.vsp (with binary file in body)
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
        result, error, status_code = handle_binary_upload(filename, binary_data)
        if error:
            return jsonify(error), status_code

        file_path = result['FilePath']

        # Open the uploaded test file
        open_result = vv_instance.OpenTest(file_path)
        
        # Start the test
        start_result = vv_instance.StartTest()
        
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

    except Exception as e:
        return jsonify(extract_com_error_info(e)), 500
    
@basic_control_bp.route('/runtest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def run_test(vv_instance):
    """
    Get Current Running Test / Run Complete Test (Open + Start)
    
    COM Method: RunTest(filepath) or OpenTest() + StartTest()
    GET: Returns current running test status
    POST: Opens a VibrationVIEW profile file and starts execution in one operation.
    
    Query Parameters (POST only):
        testname: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter
    
    Example: GET /api/runtest (returns current status)
    Example: POST /api/runtest?testname=test1.vsp or POST /api/runtest?test1.vsp
    """
    if request.method == "GET" and not request.args:
        # GET without parameters - return current running status
        is_running = vv_instance.IsRunning()
        return jsonify(success_response(
            {'result': is_running, 'is_running': is_running},
            f"Current test running status: {'Running' if is_running else 'Not running'}"
        ))
    else:
        # POST - Run test with parameters
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
        
        # Try RunTest method
        try:
            result = vv_instance.RunTest(filepath)
        except Exception as e:
            # Re-raise to be handled by @handle_errors decorator
            raise
        
        # Check if test is actually running
        success = vv_instance.IsRunning()
        
        return jsonify(success_response(
            {
                'result': success,
                'filepath': filepath,
                'executed': True
            },
            f"RunTest command {'executed successfully' if success else 'failed'}: {test_name}"
        ))

@basic_control_bp.route('/stoptest', methods=['POST'])
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
        {'result': success, 'executed': True},
        f"StopTest command {'executed successfully' if success else 'failed'}"
    ))

@basic_control_bp.route('/resumetest', methods=['POST'])
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
        {'result': success, 'executed': True},
        f"ResumeTest command {'executed successfully' if success else 'failed'}"
    ))

@basic_control_bp.route('/opentest', methods=['GET', 'POST'])
@handle_errors
@with_vibrationview
def open_test(vv_instance):
    """
    Get Current Opened Test / Open Test Profile File by Filename
    
    COM Method: OpenTest(filepath)
    GET: Returns current test ready status
    POST: Opens a VibrationVIEW profile file for execution.
    The test can then be started with StartTest.
    
    Query Parameters (POST only):
        testname: string - Test filename (named parameter)
        OR unnamed parameter: string - Test filename as first URL parameter
    
    Example: GET /api/opentest (returns current ready status)
    Example: POST /api/opentest?testname=test1.vsp or POST /api/opentest?test1.vsp
    """
    if request.method == "GET" and not request.args:
        # GET without parameters - return current ready status
        is_ready = vv_instance.IsReady()
        return jsonify(success_response(
            {'result': is_ready, 'is_ready': is_ready},
            f"Current test ready status: {'Ready' if is_ready else 'Not ready'}"
        ))
    else:
        # POST - Open test with parameters
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
        
        # Handle None return - assume success if no exception was raised
        success = True  # True if result is None or True
        
        return jsonify(success_response(
            {
                'result': success,
                'filepath': filepath,
                'executed': True
            },
            f"OpenTest command {'executed successfully' if success else 'failed'}: {test_name}"
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
    
    Example: PUT /api/opentest?filename=test1.vsp or PUT /api/opentest?test1.vsp (with binary file in body)
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