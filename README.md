# VibrationVIEW REST API

A comprehensive, modular REST interface providing 1:1 functionality with VibrationVIEW COM automation methods.

## Features

- **1:1 COM Method Mapping**: Every VibrationVIEW automation method has an exact REST endpoint
- **Modular Architecture**: Organized by functionality for easy maintenance and development
- **Thread-Safe Operations**: Supports concurrent requests in multi-user environments
- **Comprehensive Documentation**: Built-in API documentation with examples for every endpoint
- **Robust Error Handling**: Detailed COM error extraction and standardized response format
- **GET-First Design**: Prioritizes GET requests with URL parameters for simplicity
- **Bulk Operations**: Efficient batch operations for data retrieval and reporting

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your VibrationVIEW settings
```

### 3. Start the Server
```bash
# Development mode
python app.py --host 0.0.0.0 --port 5000 --debug

# Production mode
python app.py --host 0.0.0.0 --port 5000
```

### 4. Access Documentation
- **Main API Docs**: `http://localhost:5000/api/v1/docs`
- **Health Check**: `http://localhost:5000/api/v1/health`
- **Module-Specific Docs**: `http://localhost:5000/api/v1/docs/{module_name}`

## Architecture

The API is organized into functional modules with consistent patterns:

### Core Modules
- **basic_control**: Test execution, file operations, and core control
- **status_properties**: System status monitoring and state checking
- **data_retrieval**: Real-time data access (channels, demand, control, output)
- **test_control**: Advanced test control (sweeps, parameters, multipliers)
- **hardware_config**: Hardware configuration and input setup
- **gui_control**: Window management and test editing operations

### Data & Metadata Modules  
- **recording**: Data recording operations and file management
- **reporting**: Report field access with bulk operations and channel/loop support
- **auxinputs**: Auxiliary input properties and rear input metadata
- **teds**: TEDS (Transducer Electronic Data Sheet) information
- **vector_properties**: Vector metadata, units, and properties
- **utility**: Enum references and bulk data operations

## API Usage Examples

### Basic Test Control
```bash
# Start a test (existing file)
curl -X POST "http://localhost:5000/api/v1/runtest?testname=my_test.vsp"

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

### Parameter Control
```bash
# Get sine frequency
curl "http://localhost:5000/api/v1/sinefrequency"

# Set sine frequency
curl -X POST "http://localhost:5000/api/v1/sinefrequency" \
  -H "Content-Type: application/json" \
  -d '{"value": 100.0}'

# Get demand multiplier
curl "http://localhost:5000/api/v1/demandmultiplier"
```

### Hardware Configuration
```bash
# Get hardware info
curl "http://localhost:5000/api/v1/gethardwareinputchannels"
curl "http://localhost:5000/api/v1/getsoftwareversion"

# Get channel sensitivity
curl "http://localhost:5000/api/v1/inputsensitivity?1"

# Check hardware capabilities
curl "http://localhost:5000/api/v1/hardwaresupportscapacitorcoupled?0"
```

### GUI Control
```bash
# Window management
curl "http://localhost:5000/api/v1/minimize"
curl "http://localhost:5000/api/v1/maximize"
curl "http://localhost:5000/api/v1/activate"

# Test editing
curl "http://localhost:5000/api/v1/edittest?testname=test.vsp"
curl "http://localhost:5000/api/v1/abortedit"
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

### Utility Operations
```bash
# Get enum references
curl "http://localhost:5000/api/v1/enums/all"
curl "http://localhost:5000/api/v1/enums/vvvector"

# Connection diagnostics
curl "http://localhost:5000/api/v1/debug/connectioninfo"
```

## Request Patterns

### GET Requests (Preferred)
Most endpoints use GET requests with URL parameters:
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

# With JSON body
curl -X POST "http://localhost:5000/api/v1/demandmultiplier" \
  -H "Content-Type: application/json" \
  -d '{"value": 6.0}'

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
    "result": "actual_value",
    "executed": true
  },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-31T10:30:00"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "error_code": "ERROR_TYPE",
  "timestamp": "2025-01-31T10:30:00"
}
```

## Development

### Project Structure
```
vibrationview_api/
├── app.py                    # Main application with health checks
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── routes/                   # Route modules (1:1 COM mapping)
│   ├── __init__.py          # Blueprint exports
│   ├── basic_control.py     # Core test operations
│   ├── status_properties.py # Status monitoring
│   ├── data_retrieval.py    # Real-time data access
│   ├── test_control.py      # Advanced test control
│   ├── hardware_config.py   # Hardware configuration
│   ├── gui_control.py       # Window management
│   ├── recording.py         # Data recording
│   ├── reporting.py         # Report field access
│   ├── auxinputs.py         # Auxiliary inputs
│   ├── teds.py              # TEDS information
│   ├── vector_properties.py # Vector metadata
│   ├── utility.py           # Enums and utilities
│   └── common.py            # Shared utilities
├── utils/                    # Utility modules
│   ├── vv_manager.py        # VibrationVIEW connection management
│   ├── response_helpers.py  # Response formatting
│   ├── decorators.py        # Common decorators
│   └── utils.py             # General utilities
├── tests/                    # Unit tests
├── docs/                     # Additional documentation
└── scripts/                  # Utility scripts
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

### Key Design Principles

- **1:1 COM Mapping**: Every REST endpoint maps directly to a VibrationVIEW COM method
- **GET-First**: Use GET requests with URL parameters when possible
- **Consistent Responses**: Standardized success/error response format
- **Thread Safety**: All VibrationVIEW operations use proper connection management
- **Comprehensive Documentation**: Every endpoint includes COM method signature and examples
- **Error Transparency**: COM errors are extracted and returned with full context

## Advanced Features

### Bulk Operations
Efficient operations that combine multiple COM calls:
- `POST /api/v1/reportfields` - Multiple report fields with channel/loop support
- `GET /api/v1/allstatus` - All status flags in single request
- `GET /api/v1/enums/all` - All enumeration constants

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

## Configuration

### Environment Variables (.env)
```bash
# API Configuration
API_VERSION=1.0.0
SECRET_KEY=your-secret-key

# CORS Settings  
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO

# VibrationVIEW Settings
VV_CONNECTION_TIMEOUT=10.0
VV_RETRY_ATTEMPTS=5
VV_MAX_INSTANCES=5

# Paths
PROFILE_FOLDER=C:\VibrationVIEW\Profiles
REPORT_FOLDER=C:\VibrationVIEW\Reports
```

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
   curl "http://localhost:5000/api/v1/testreporting" 
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