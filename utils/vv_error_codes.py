# ============================================================================
# FILE: utils/vv_error_codes.py
# ============================================================================

"""
VibrationVIEW HRESULT Error Codes

These constants match the VibrationVIEW COM interface error codes.
MAKE_HRESULT formula: ((SEVERITY << 31) | (FACILITY << 16) | CODE)
- SEVERITY_ERROR = 1, SEVERITY_SUCCESS = 0
- FACILITY_ITF = 4

Error codes (SEVERITY_ERROR): 0x80040000 | code
Success codes (SEVERITY_SUCCESS): 0x00040000 | code

Values are represented as signed 32-bit integers for Python compatibility.
"""

# DISP_E_EXCEPTION - wrapper error when COM raises an exception
DISP_E_EXCEPTION = -2147352567  # 0x80020009

# VibrationVIEW Error Codes (SEVERITY_ERROR, FACILITY_ITF)
VVIEW_E_ALREADY_RUNNING = -2147220992          # 0x80040200
VVIEW_E_TEST_NOT_FOUND = -2147220990           # 0x80040202
VVIEW_E_KEY_NOT_FOUND = -2147220989            # 0x80040203
VVIEW_E_NO_SUCH_DIRECTORY = -2147220988        # 0x80040204
VVIEW_E_CANT_CREATE_FILE = -2147220987         # 0x80040205
VVIEW_E_FILE_EXISTS = -2147220986              # 0x80040206
VVIEW_E_STRING_CONVERSION_FAILED = -2147220984 # 0x80040208
VVIEW_E_NO_DATA = -2147220983                  # 0x80040209
VVIEW_E_WAITING_FOR_BOX = -2147220981          # 0x8004020b
VVIEW_E_ACTIVEX_KEYMISSING = -2147220980       # 0x8004020c
VVIEW_E_UNDEFINED = -2147220979                # 0x8004020d
VVIEW_E_WRONG_NUMBER_DIMS = -2147220978        # 0x8004020e
VVIEW_E_WRONG_DATATYPE = -2147220977           # 0x8004020f
VVIEW_E_TED_TEMPLATE_MISSING = -2147220976     # 0x80040210
VVIEW_E_RECORDING = -2147220975                # 0x80040211
VVIEW_E_FAILEDTOSAVE = -2147220974             # 0x80040212
VVIEW_E_WINDOWSERROR = -2147220972             # 0x80040214
VVIEW_E_BADPARAMETER = -2147220971             # 0x80040215
VVIEW_E_WRONGTESTMODE = -2147220970            # 0x80040216
VVIEW_E_TRANSIENT_KEYMISSING = -2147220969     # 0x80040217
VVIEW_E_LENGTH_MISMATCH = -2147220968          # 0x80040218
VVIEW_E_FAILED_INPUT_CONFIG = -2147220967      # 0x80040219
VVIEW_E_UNEXPECTED = -2147220966               # 0x8004021a
VVIEW_E_MISMATCH = -2147220965                 # 0x8004021b
VVIEW_E_PRETESTCANTRESUME = -2147220964        # 0x8004021c
VVIEW_E_DATABASE_NOT_AVAILABLE = -2147220963   # 0x8004021d

# VibrationVIEW Success Codes (SEVERITY_SUCCESS, FACILITY_ITF)
VVIEW_S_NOT_RUNNING = 262657                   # 0x00040201
VVIEW_S_NO_DIALOG_OPEN = 262663                # 0x00040207
VVIEW_S_SHORTER_THAN_REQUESTED = 262666        # 0x0004020a
VVIEW_S_WAITING_FOR_BOX = 262675               # 0x00040213

# Error names mapping (human-readable strings)
ERROR_NAMES = {
    DISP_E_EXCEPTION: 'COM dispatch exception',
    VVIEW_E_ALREADY_RUNNING: 'Test is already running',
    VVIEW_S_NOT_RUNNING: 'Test is already stopped',
    VVIEW_E_TEST_NOT_FOUND: 'Test not found',
    VVIEW_E_KEY_NOT_FOUND: 'Key not found',
    VVIEW_E_NO_SUCH_DIRECTORY: 'No such directory',
    VVIEW_E_CANT_CREATE_FILE: "Can't create file",
    VVIEW_E_FILE_EXISTS: 'File exists',
    VVIEW_S_NO_DIALOG_OPEN: 'No dialog open',
    VVIEW_E_STRING_CONVERSION_FAILED: 'String conversion failed',
    VVIEW_E_NO_DATA: 'No data available',
    VVIEW_S_SHORTER_THAN_REQUESTED: 'Vector was shorter than requested',
    VVIEW_E_WAITING_FOR_BOX: 'Waiting for IOBox to initialize error',
    VVIEW_E_ACTIVEX_KEYMISSING: 'Automation Interface Software option is not enabled',
    VVIEW_E_UNDEFINED: 'Undefined Error',
    VVIEW_E_WRONG_NUMBER_DIMS: 'Wrong number of dimensions in requested array',
    VVIEW_E_WRONG_DATATYPE: 'Return array has improper datatype',
    VVIEW_E_TED_TEMPLATE_MISSING: 'TEDs template file not found',
    VVIEW_E_RECORDING: 'Recording is already running',
    VVIEW_E_FAILEDTOSAVE: 'File failed to save',
    VVIEW_S_WAITING_FOR_BOX: 'Waiting for IOBox to initialize warning',
    VVIEW_E_WINDOWSERROR: 'Windows returned an error',
    VVIEW_E_BADPARAMETER: 'Passed an invalid parameter value',
    VVIEW_E_WRONGTESTMODE: 'Wrong test mode for requested operation',
    VVIEW_E_TRANSIENT_KEYMISSING: 'Transient Caption Software option is not enabled',
    VVIEW_E_LENGTH_MISMATCH: 'Length mismatch',
    VVIEW_E_FAILED_INPUT_CONFIG: 'Failed loading input configuration',
    VVIEW_E_UNEXPECTED: 'Unexpected error',
    VVIEW_E_MISMATCH: 'Data mismatch',
    VVIEW_E_PRETESTCANTRESUME: "Can't resume after pretest",
    VVIEW_E_DATABASE_NOT_AVAILABLE: 'Database not available',
}


def get_error_name(hr_or_scode):
    """Get the error constant name for a given HRESULT or scode value"""
    return ERROR_NAMES.get(hr_or_scode, f'UNKNOWN_ERROR_{hr_or_scode}')


def get_scode_from_exception(e):
    """Extract scode from a COM exception if available"""
    if hasattr(e, 'args') and len(e.args) >= 3:
        exc_info = e.args[2]
        if isinstance(exc_info, tuple) and len(exc_info) > 5:
            return exc_info[5]  # scode is at index 5
    return None


def is_vview_error(e, error_code):
    """Check if exception matches a specific VibrationVIEW error code"""
    scode = get_scode_from_exception(e)
    return scode == error_code


def get_error_info(e):
    """Get error code and name from a COM exception"""
    scode = get_scode_from_exception(e)
    if scode is not None:
        return {
            'code': scode,
            'name': get_error_name(scode)
        }
    return None
