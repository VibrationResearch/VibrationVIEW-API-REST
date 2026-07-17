# VibrationVIEW REST API

A comprehensive, modular REST interface providing 1:1 functionality with VibrationVIEW COM automation methods.

## Features

- **1:1 COM Method Mapping**: Every VibrationVIEW automation method has an exact REST endpoint
- **Modular Architecture**: Organized by functionality for easy maintenance and development
- **Thread-Safe Operations**: Supports concurrent requests in multi-user environments
- **Comprehensive Documentation**: Built-in API documentation with examples for every endpoint
- **Robust Error Handling**: Detailed COM error extraction and standardized response format
- **REST Conventions**: GET for queries, POST for state-changing operations
- **Bulk Operations**: Efficient batch operations for data retrieval and reporting

## Requirements

- Windows operating system (compatible with Windows 10 and Windows 11)
- VibrationVIEW software installed
- VibrationVIEW automation option (VR9604) - OR - VibrationVIEW may be run in Demonstration mode without any additional hardware or software

## Deployment

Download the latest release zip from https://github.com/VibrationResearch/VibrationVIEW-API-REST/releases and follow the [SETUP-README](SETUP-README.md) instructions.

## Quick Start (from source)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure VibrationVIEW
VibrationVIEW must be installed and configured, but does not need to be running before starting the server.

- **With hardware**: Configure VibrationVIEW for your controller
- **Demonstration mode**: Download and install from https://vibrationresearch.com/download-demo/. When prompted, request a demo activation code. Once activated, you can run simulated tests without a physical controller.

### 3. Configure Environment
```bash
copy .env.example .env
```
Generate secure values for `SECRET_KEY` and `API_KEY`:
   ```cmd
   powershell -Command "$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); -join ($b | ForEach-Object { '{0:X2}' -f $_ })"
   ```
   Run the command twice and paste each output into `.env` — once for `SECRET_KEY` and once for `API_KEY`. 
   Set `API_KEY` to empty to disable Bearer token authentication during development.

### 4. Start the Server
```bash
python app.py --debug
```

### 5. Access Documentation
- **Main API Docs**: `http://localhost:5000/api/v1/docs`
- **Health Check**: `http://localhost:5000/api/v1/health`
- **Module-Specific Docs**: `http://localhost:5000/api/v1/docs/{module_name}`

## Architecture

The API is organized into functional modules with consistent patterns:

### Core Modules
- **basic_control**: Test execution, file operations, and core control
- **status_properties**: System status monitoring and state checking
- **data_retrieval**: Real-time data access (channels, demand, control, output)
- **advanced_control**: Advanced test control (test type)
- **advanced_control_sine**: Sine-specific controls (sweeps, parameters, multipliers)
- **hardware_config**: Hardware configuration
- **input_config**: Input channel configuration, calibration, and transducer database
- **gui_control**: Window management and test editing operations

### Data & Metadata Modules
- **recording**: Data recording operations and file management
- **reporting**: Report field access with bulk operations and channel/loop support
- **report_generation**: Report generation, data export (CSV, TXT, UFF), and data file retrieval
- **auxinputs**: Auxiliary input properties and rear input metadata
- **teds**: TEDS (Transducer Electronic Data Sheet) information
- **vector_properties**: Vector metadata, units, and properties
- **virtual_channels**: Virtual channel management (import, remove all)
- **log**: Event log retrieval in structured JSON format

## API Usage Examples

> **Note:** If `API_KEY` is configured, all requests must include the header `-H "Authorization: Bearer <your-api-key>"`. 
This header is omitted from the examples below for brevity.

### Basic Test Control
```bash
# Start a test (existing file)
curl -X POST "http://localhost:5000/api/v1/runtest?filename=my_test.vsp"

# Stop a test
curl -X POST "http://localhost:5000/api/v1/stoptest"

# Check if running
curl "http://localhost:5000/api/v1/isrunning"

# Upload and run test file
curl -X PUT "http://localhost:5000/api/v1/runtest?filename=test.vsp" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.vsp
```

### Status Monitoring
```bash
# Get comprehensive status
curl "http://localhost:5000/api/v1/status"

# Check hardware readiness
curl "http://localhost:5000/api/v1/isready"

# Get all status flags at once
curl "http://localhost:5000/api/v1/allstatus"
```

### Real-Time Data Access
```bash
# Get channel data
curl "http://localhost:5000/api/v1/channel"

# Get control values
curl "http://localhost:5000/api/v1/control"

# Get demand values  
curl "http://localhost:5000/api/v1/demand"

# Get output values
curl "http://localhost:5000/api/v1/output"
```

### Sine Control
```bash
# Get sine frequency
curl "http://localhost:5000/api/v1/sinefrequency"

# Set sine frequency
curl -X POST "http://localhost:5000/api/v1/sinefrequency?value=100.0"
```

### Hardware Configuration
```bash
# Get hardware info
curl "http://localhost:5000/api/v1/gethardwareinputchannels"
curl "http://localhost:5000/api/v1/getsoftwareversion"

# Get channel sensitivity
curl "http://localhost:5000/api/v1/inputsensitivity?1"

# Check hardware capabilities
curl "http://localhost:5000/api/v1/hardwaresupportscapacitorcoupled?1"
```

### GUI Control
```bash
# Window management
curl -X POST "http://localhost:5000/api/v1/minimize"
curl -X POST "http://localhost:5000/api/v1/maximize"
curl -X POST "http://localhost:5000/api/v1/activate"
```

### Reporting (Advanced)
```bash
# Get single report field
curl "http://localhost:5000/api/v1/reportfield?field=TestName"

# Get multiple fields with channel/loop support
curl -X POST "http://localhost:5000/api/v1/reportfields?channel=all&loop=1" \
  -H "Content-Type: application/json" \
  -d '{"fields": ["MaxLevel", "RMS", "TestResult"]}'

# Response format includes separated values and metadata:
# {
#   "results": {
#     "MaxLevel": [
#       {"value": "5.2 g", "channel": 1, "loop": 1},
#       {"value": "4.8 g", "channel": 2, "loop": 1}
#     ]
#   }
# }
```

### Report Generation & Data Export
```bash
# Generate a report from VibrationVIEW data
curl -X POST "http://localhost:5000/api/v1/generatereport" \
  -H "Content-Type: application/json" \
  -d '{"templatename": "Test Report.vvtemplate", "outputname": "report.docx"}'

# Generate text file from data (one file per plot)
curl -X POST "http://localhost:5000/api/v1/generatetxt" \
  -H "Content-Type: application/json" \
  -d '{"outputname": "data.txt"}'

# Generate UFF (Universal File Format) from data
curl -X POST "http://localhost:5000/api/v1/generateuff" \
  -H "Content-Type: application/json" \
  -d '{"outputname": "data.uff"}'

# Get raw data file (.vrd)
curl "http://localhost:5000/api/v1/datafile" --output data.vrd

# Get all data files from last test as zip
curl "http://localhost:5000/api/v1/datafiles" --output test_data.zip

# Upload and generate report in one operation
curl -X POST "http://localhost:5000/api/v1/generatereport?templatename=Standard%20Report&outputname=report.pdf" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @test.vrd
```

### Virtual Channels
```bash
# Import virtual channels from file
curl -X POST "http://localhost:5000/api/v1/importvirtualchannels?filename=channels.vvc"

# Upload and import virtual channels
curl -X PUT "http://localhost:5000/api/v1/importvirtualchannels?filename=channels.vvc" \
  -H "Content-Type: application/octet-stream" \
  --data-binary @channels.vvc

# Remove all virtual channels
curl -X POST "http://localhost:5000/api/v1/removeallvirtualchannels"
```

### Event Log
```bash
# Get event log as structured JSON
curl "http://localhost:5000/api/v1/log"
```

### Report Fields History
```bash
# Get report fields for all data files from last test
curl "http://localhost:5000/api/v1/reportfieldshistory?fields=StopCode,RunTime,Time"

# With POST
curl -X POST "http://localhost:5000/api/v1/reportfieldshistory" \
  -H "Content-Type: application/json" \
  -d '{"fields": ["StopCode", "RunTime", "Time"]}'
```

### Utility Operations
```bash
# Vector enumeration reference (for use with /vector endpoint)
curl "http://localhost:5000/api/v1/docs/vector_enums"

# Connection diagnostics
curl "http://localhost:5000/api/v1/testcom"
```

## Request Patterns

### GET Requests
Read-only endpoints use GET requests with URL parameters:
```bash
# Single parameter
curl "http://localhost:5000/api/v1/reportfield?field=TestName"

# Multiple parameters  
curl "http://localhost:5000/api/v1/inputsensitivity?1"

# Boolean parameters
curl "http://localhost:5000/api/v1/inputcapacitorcoupled?1&true"
```

### POST Requests
Used for operations that modify state or require complex parameters:
```bash
# Simple operations
curl -X POST "http://localhost:5000/api/v1/starttest"

# With URL parameter
curl -X POST "http://localhost:5000/api/v1/demandmultiplier?value=6.0"

# Bulk operations
curl -X POST "http://localhost:5000/api/v1/reportfields" \
  -H "Content-Type: application/json" \
  -d '{"fields": ["TestName", "Duration", "MaxLevel"]}'
```

## Response Format

All endpoints return consistent JSON responses:

### Success Response
```json
{
  "success": true,
  "data": {
    "result": "actual_value"
  },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-31T10:30:00+00:00"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_TYPE",
  "timestamp": "2025-01-31T10:30:00+00:00"
}
```

## Development

### Project Structure
```
vibrationview_api/
├── app.py                    # Main application with health checks
├── config.py                 # Configuration management
├── requirements.in           # Direct dependencies (human-editable)
├── requirements.txt          # Fully locked dependencies (generated by pip-compile)
├── setup.bat                 # Offline setup (Command Prompt)
├── setup.ps1                 # Offline setup (PowerShell)
├── start-api.bat             # Start the server (Command Prompt)
├── prepare-offline.ps1       # Build deployment zip with vendored packages
├── .env.example              # Environment variable template
├── SETUP-README.md           # Offline deployment guide (included in zip)
├── routes/                   # Route modules (1:1 COM mapping)
│   ├── __init__.py          # Blueprint exports
│   ├── basic_control.py     # Core test operations
│   ├── status_properties.py # Status monitoring
│   ├── data_retrieval.py    # Real-time data access
│   ├── advanced_control.py  # Advanced test control
│   ├── advanced_control_sine.py # Sine-specific advanced control
│   ├── advanced_control_system_check.py # System check controls
│   ├── hardware_config.py   # Hardware configuration
│   ├── input_config.py      # Input channel configuration
│   ├── gui_control.py       # Window management
│   ├── recording.py         # Data recording
│   ├── reporting.py         # Report field access
│   ├── report_generation.py # Report/data file generation
│   ├── virtual_channels.py  # Virtual channel management
│   ├── log.py               # Event log retrieval
│   ├── aux_inputs.py        # Auxiliary inputs
│   ├── teds.py              # TEDS information
│   └── vectors_legacy.py    # Vector metadata
├── utils/                    # Utility modules
│   ├── vv_manager.py        # VibrationVIEW connection management
│   ├── vv_singleton.py       # VibrationVIEW instance singleton
│   ├── vv_error_codes.py    # VibrationVIEW error code definitions
│   ├── response_helpers.py  # Response formatting
│   ├── decorators.py        # Common decorators
│   ├── path_validator.py    # File path security validation
│   ├── teds_formatter.py    # TEDS data formatting utilities
│   └── utils.py             # General utilities
├── templates/                # Test profile templates
├── tests/                    # Unit tests
└── docs/                     # Additional documentation
    └── Endpoint-Automation-CrossReference.md  # REST endpoint to Automation method cross-reference
```

### Adding New Endpoints

1. **Choose the appropriate module** based on functionality
2. **Follow the established pattern**:
   ```python
   @module_bp.route('/endpoint', methods=['GET'])
   @handle_errors
   @with_vibrationview  
   def endpoint_function(vv_instance):
       """COM Method: MethodName() - Description"""
       result = vv_instance.MethodName()
       return jsonify(success_response({'result': result}))
   ```
3. **Update module documentation** in the `/docs/{module}` endpoint
4. **Add tests** in the corresponding test file
5. **Update this README** if needed

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/test_basic_control.py

# Run with coverage
pytest --cov=routes tests/
```

### Updating Dependencies

Production dependencies are managed with [pip-tools](https://pip-tools.readthedocs.io/). Edit `requirements.in` to change direct dependencies, then regenerate the locked `requirements.txt`:
```bash
pip-compile requirements.in
```
This pins every package (including transitive dependencies) to exact versions for reproducible builds. Never edit `requirements.txt` by hand.

### Key Design Principles

- **1:1 COM Mapping**: Every REST endpoint maps directly to a VibrationVIEW COM method
- **REST Conventions**: GET for queries, POST for state-changing operations
- **Consistent Responses**: Standardized success/error response format
- **Thread Safety**: All VibrationVIEW operations use proper connection management
- **Comprehensive Documentation**: Every endpoint includes COM method signature and examples
- **Error Transparency**: COM errors are extracted and returned with full context

## Advanced Features

### Bulk Operations
Efficient operations that combine multiple COM calls:
- `POST /api/v1/reportfields` - Multiple report fields with channel/loop support
- `POST /api/v1/reportfieldshistory` - Report fields for all data files from last test
- `GET /api/v1/allstatus` - All status flags in single request
- `GET /api/v1/docs/vector_enums` - Vector enumeration reference
- `GET /api/v1/datafiles` - All data files from last test as zip archive
- `GET /api/v1/log` - Event log as structured JSON array

### Channel/Loop Support
Advanced reporting with automatic field name formatting:
```bash
# Get MaxLevel for all channels
curl -X POST "http://localhost:5000/api/v1/reportfields?channel=all" \
  -d '{"fields": ["MaxLevel"]}'

# Results in COM calls: MaxLevel1:, MaxLevel2:, MaxLevel3:, etc.
```

### File Upload Support
Binary file uploads for test profiles:
```bash
curl -X PUT "http://localhost:5000/api/v1/runtest?filename=test.vsp" \
  -H "Content-Length: $(stat -c%s test.vsp)" \
  --data-binary @test.vsp
```

### Data Export Support
Export test data in multiple formats:
- **Reports**: Generate formatted reports using templates (RTF, PDF, HTML, etc.)
- **Text Files**: Export plot data as CSV-style text files (one file per plot)
- **UFF Files**: Export in Universal File Format for analysis tools
- **Raw Data**: Download .vrd files directly or as zip archives

### Virtual Channel Management
Import and manage virtual channels programmatically:
```bash
# Import virtual channels configuration
curl -X POST "http://localhost:5000/api/v1/importvirtualchannels?filename=channels.vvc"

# Remove all virtual channels
curl -X POST "http://localhost:5000/api/v1/removeallvirtualchannels"
```

## Configuration

### Secret Key
The `SECRET_KEY` is used by Flask for cryptographic signing. In production mode, the server will refuse to start if `SECRET_KEY` is still set to the development default. Generate a secure value:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### API Key Authentication
All requests must include an `Authorization: Bearer <key>` header. To set up:

1. Generate a key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Set `API_KEY` in your `.env` file to the generated value.
3. Configure the same key on the controller PC (outside of source control).

If `API_KEY` is empty or not set, authentication is disabled.

### Write Guard (ALLOW_GET_WRITE)
By default, state-changing endpoints (`starttest`, `stoptest`, `savedata`, `recordstart`, etc.) reject GET requests with 405 and require POST. This follows REST conventions and prevents accidental triggers from browser navigation.

Set `ALLOW_GET_WRITE=true` in `.env` to allow GET on these endpoints for backward compatibility or demonstrations.

### Upload Size Limit (MAX_CONTENT_LENGTH)
Flask rejects request bodies larger than `MAX_CONTENT_LENGTH` (default: 10 MB) before they reach application code, preventing memory exhaustion from oversized uploads. Set in `.env` to override:

```
MAX_CONTENT_LENGTH=10485760
```

### Environment Variables (.env)
```bash
# API Configuration
API_VERSION=1.0.0
SECRET_KEY=your-secret-key

# CORS Settings — restricts browser-based cross-origin requests.
CORS_ORIGINS=http://127.0.0.1

# API Key Authentication
API_KEY=replace-with-generated-key

# Write Guard — block GET on state-changing endpoints (default: false)
ALLOW_GET_WRITE=false

# Logging
LOG_LEVEL=INFO
# VV_LOG_DIR=C:\ProgramData\VibrationVIEW\logs
# VV_LOG_MAX_BYTES=5242880
# VV_LOG_BACKUP_COUNT=5

# VibrationVIEW Settings
VV_CONNECTION_TIMEOUT=10.0
VV_RETRY_ATTEMPTS=5
VV_MAX_INSTANCES=5

# Paths
PROFILE_FOLDER=C:\VibrationVIEW\Profiles
REPORT_FOLDER=C:\VibrationVIEW\Reports
```

## Production Deployment

### Configure Waitress to Bind to the VLAN Interface IP

By default `start-api.bat` binds to `127.0.0.1`. To accept connections from the controller PC, use `--host` with the VLAN adapter IP:
```
start-api.bat --host 192.168.1.10 --port 5000
```
Do not use `0.0.0.0`, which would expose the API on all network interfaces.

### Add a Firewall Rule to Restrict Access to the Controller PC

From an elevated command prompt on the VibrationVIEW PC:
```
netsh advfirewall firewall add rule name="VibrationVIEW REST API" dir=in action=allow protocol=TCP localport=5000 remoteip=192.168.1.20
```
Replace `5000` with the Waitress port and `192.168.1.20` with the controller PC's IP address.

## Troubleshooting

### Common Issues

1. **COM Connection Failures**
   ```bash
   # Test basic connectivity
   curl "http://localhost:5000/api/v1/testcom"
   
   # Check hardware status
   curl "http://localhost:5000/api/v1/isready"
   ```

2. **Module-Specific Diagnostics**
   ```bash
   # Test specific modules
   curl "http://localhost:5000/api/v1/allstatus"
   curl "http://localhost:5000/api/v1/testrecording"
   ```

3. **Get Available Endpoints**
   ```bash
   # Main documentation
   curl "http://localhost:5000/api/v1/docs"
   
   # Module documentation  
   curl "http://localhost:5000/api/v1/docs/basic_control"
   curl "http://localhost:5000/api/v1/docs/reporting"
   ```

## License

This work is licensed under the Creative Commons Attribution 4.0 International License. To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/ or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.

### You are free to:
- **Share** — copy and redistribute the material in any medium or format
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially

### Under the following terms:
- **Attribution** — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.

**No additional restrictions** — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.

### Notices:
You do not have to comply with the license for elements of the material in the public domain or where your use is permitted by an applicable exception or limitation.

No warranties are given. The license may not give you all of the permissions necessary for your intended use. For example, other rights such as publicity, privacy, or moral rights may limit how you use the material.