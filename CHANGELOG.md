# Changelog

All notable changes to the VibrationVIEW REST API are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.1.0] - Unreleased

### Breaking Changes

- **UTC timestamps**: All API response timestamps now use UTC with an explicit `+00:00` offset (e.g., `2026-06-19T18:30:00+00:00`). Previously, timestamps used local time without a timezone indicator. Update any client-side parsing that assumes local time. (#18)
- **1-based channel indexing**: Hardware capability endpoints (`hardwaresupportscapacitorcoupled`, `hardwaresupportsaccelpowersource`, `hardwaresupportsdifferential`) now use 1-based channel indexing, consistent with all other channel-based endpoints. Previously these used 0-based indexing. Clients passing channel 0 must update to channel 1. (#15)
- **Standardized response keys for `/closetest` and `/closetab`**: The `test_was_closed` key in response `data` has been renamed to `result` for consistency with all other endpoints. Clients reading `data.test_was_closed` must update to `data.result`.
- **Removed `executed` key and fixed `result` for GUI control responses**: `/abortedit`, `/minimize`, `/restore`, `/maximize`, and `/activate` no longer include `data.executed` and now return `data.result: true` instead of `data.result: null`. Previously these void COM methods returned `null` for `result`.
- **POST-only state-changing endpoints**: Endpoints that modify state (e.g., `starttest`, `stoptest`, `savedata`) now require POST requests by default. GET requests return 405. Set `ALLOW_GET_WRITE=true` to restore the previous behavior during migration. (#12)
- **Simplified configuration**: Removed `DevelopmentConfig`, `ProductionConfig`, and the config map. A single `Config` class is used for all environments; use `--debug` flag to enable debug mode. Production startup validates that `SECRET_KEY` and `API_KEY` are not set to insecure defaults. (#19)
- **Renamed query parameters** (#16): The following query parameter and JSON body key names have changed:

  | Old Name | New Name | Endpoints |
  |----------|----------|-----------|
  | `channelnum` | `channel` | `/channelunit`, `/channellabel` |
  | `loopnum` | `loop` | `/controlunit`, `/controllabel` |
  | `file_path` | `filename` | `/getdatafile`, `/datafile`, `/generatereport`, `/generatetxt`, `/generateuff` |
  | `template_name` | `templatename` | `/generatereport` |
  | `output_name` | `outputname` | `/generatereport`, `/generatetxt`, `/generateuff` |

- **Renamed response fields** (#16):

  | Old Field | New Field | Endpoints |
  |-----------|-----------|-----------|
  | `data.channelnum` | `data.channel` | `/channelunit`, `/channellabel` |
  | `data.loopnum` | `data.loop` | `/controlunit`, `/controllabel` |
  | `data.internal_loopnum` | `data.internal_loop` | `/controllabel` |

- **Standardized error messages** (#16): Missing-parameter errors now use the format `"Missing required parameter: <name>"` instead of `"Missing required query parameter: <name>"`.
- **Standardized error response format** (#16): Error responses from `/rearinputunit` and `/rearinputlabel` now use the structured format `"error": {"code": "...", "message": "..."}` consistent with all other endpoints.
- **Standardized file upload error responses** (#64): File upload error responses previously returned `{"Error": "..."}`. They now use the standard API format `{"success": false, "error": {"code": "UPLOAD_ERROR", "message": "..."}, "timestamp": "..."}`. Clients parsing the old `Error` key must update to use `error.message`.

### Security

- **API key authentication**: All endpoints (except `/health` and `/docs`) require an `Authorization: Bearer <key>` header when `API_KEY` is configured. Auth is disabled when `API_KEY` is empty, so existing deployments are unaffected until configured. (#5)
- **CORS origin restriction**: Default `CORS_ORIGINS` changed from `*` (allow all) to `http://127.0.0.1`. Configure `CORS_ORIGINS` in `.env` for your deployment. (#4)
- **Upload size limit**: Uploads limited to 10 MB by default via `MAX_CONTENT_LENGTH`. Oversized requests receive a 413 JSON response. (#7)
- **Filename sanitization**: Uploads with empty, special-character-only, non-ASCII-only, or double-extension filenames are rejected with a 400 response after `secure_filename` processing. (#6)
- **Production key validation**: Server refuses to start in production mode if `SECRET_KEY` or `API_KEY` are set to development defaults. (#19)
- **Config import fix**: Fixed `AttributeError` on `config.EXE_NAME` by standardizing all imports to `from config import Config`. (#9)

### Improvements

- **VibrationVIEW singleton extraction**: Extracted VibrationVIEW instance management into `utils/vv_singleton.py` with `IsReady()` gate, explicit COM object cleanup on shutdown, and improved thread safety. (#20)
- **Datafiles parsing**: `/datafiles` endpoint now requests only `LastData` from `ReportFieldsHistory` for more efficient single-file retrieval. (#21)
- **Type hints**: Added type annotations across route handlers, utility modules, `config.py`, and `app.py` for mypy compliance. (#26)
- **Docs accuracy**: Updated docs endpoints to show POST for state-changing operations; fixed stale references. (#24)
- **CI workflow**: Added GitHub Actions CI with mypy type checking and pytest. (#61)
- **Mypy compliance**: Fixed type errors across `data_retrieval`, `input_config`, `reporting`, and utility modules. (#61)
- **Consistent parameter parsing**: All query parameters use shared helpers (`get_query_param`, `get_query_param_string`) supporting both named and unnamed styles. (#16)
- **Centralized NaN/Inf handling**: Custom Flask JSON provider automatically converts NaN and Inf to `null` in all responses. (#17)
- **Centralized error handling**: Improved exception handling with `APIError` and COM error formatting. (#14)
- **File upload refactoring**: Extracted `process_file_upload()` helper combining `detect_file_upload()` and `handle_binary_upload()`. Both now raise `APIError` instead of returning error tuples, reducing upload boilerplate across 5 route modules. (#64)
- **Duplicate handler fix**: Merged two conflicting route handlers for `/importvirtualchannels` into a single POST/PUT handler. (#11)
- **Insomnia submodule**: Extracted the Insomnia collection into a separate git submodule. (#34)
- **Ruff migration**: Replaced flake8, black, and isort with ruff for linting, formatting, and import sorting. (#25)
- **Path validation**: Confirmed case-insensitive on Windows via `PureWindowsPath.relative_to`. (#8)
- **Logging configuration**: Added `RotatingFileHandler` with configurable log directory. (#10)

### Bug Fixes

- **Test fixes**: Mocked `handle_binary_upload` in report generation tests so they no longer depend on local filesystem paths. (#46)
- **Test auth fix**: Disabled API key auth in `TestingConfig` so `.env` API_KEY values don't cause test failures. (#37)

## [1.0.0] - 2026-05-29

### Added

- Waitress WSGI server for production deployment (replacing Flask development server)
- Early binding for VibrationVIEW COM connection at startup
- Offline installation package with PowerShell script
- TEDS configuration documentation and step-by-step REST API workflow
- Endpoint-to-COM function cross reference documentation
- SETUP-README with deployment and configuration instructions
- Channel Report Fields documentation
- `channel=all` option for `/reportfields` endpoint
- Additional diagnostics to `/health` endpoint
- Support for VibrationVIEW 2026.1 file extensions (`.vyp`, `.vyd`) in input config
- Example system check profile and VIC configuration files

### Improved

- TEDS channel status error handling via `_teds_read_channel_status`
- Test suite runs on localhost rather than all network interfaces
- Removed not-implemented `GET /api/v1/inputconfigurationfile` endpoint
- Updated README with file descriptions and requirements

### Fixed

- Test fixtures for early binding compatibility

## [2025.4.3] - 2025-12-31

### Added

- Initial REST API with 1:1 mapping to VibrationVIEW COM automation methods
- Route modules: basic control, status properties, data retrieval, advanced control, hardware config, GUI control, recording, reporting, aux inputs, TEDS, vector properties
- Modular Flask Blueprint architecture
- Singleton VibrationVIEW instance management with thread-safe access
- Error handling decorators (`@handle_errors`, `@with_vibrationview`)
- Standardized JSON response format across all endpoints
- Environment-based configuration with `.env` support
- CORS support via flask-cors
- Mock VibrationVIEW API for unit testing
- Insomnia collection for API testing
- Report generation endpoints (RTF, PDF, TXT, UFF, MAT)
- File upload handling with `handle_binary_upload` and `detect_file_upload`
- Virtual channel import/export support
- Input configuration file upload and management
- TEDS read, verify, and apply operations
- Database API functions
- ReportFields, ReportVector, and ReportFieldsHistory endpoints
- Named and unnamed query parameter support
- Sanitized NaN values in JSON responses
- Path validation for file operations
- Configurable profile, report, and data folders

[1.1.0]: https://github.com/VibrationResearch/VibrationVIEW-API-REST/compare/1.0.0...HEAD
[1.0.0]: https://github.com/VibrationResearch/VibrationVIEW-API-REST/compare/2025.4.3...1.0.0
[2025.4.3]: https://github.com/VibrationResearch/VibrationVIEW-API-REST/releases/tag/2025.4.3
