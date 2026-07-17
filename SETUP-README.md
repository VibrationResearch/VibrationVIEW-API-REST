# VibrationVIEW REST API — Setup Guide

## Prerequisites

- **Windows** machine
- **VibrationVIEW** installed on the target machine
- VibrationVIEW automation option (VR9604) — or VibrationVIEW may be run in Demonstration mode without any additional hardware or software

## Quick Start

1. Extract the release zip to a folder on the target machine.
2. Copy `.env.example` to `.env` and edit it to match your environment.
   At minimum, generate secure values for `SECRET_KEY` and `API_KEY`:

   ```cmd
   powershell -Command "$b = New-Object byte[] 32; [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b); -join ($b | ForEach-Object { '{0:X2}' -f $_ })"
   ```

   Run the command twice and paste each output into `.env` 
   — once for `SECRET_KEY` 
   — once for`API_KEY`
   The server will refuse to start in production mode if either key is still set to its default placeholder.

3. Run the executable:

```cmd
VibrationVIEW-API.exe
VibrationVIEW-API.exe --port 8080
VibrationVIEW-API.exe --debug
VibrationVIEW-API.exe --host 127.0.0.1 --port 5000 --threads 8
```

No Python installation or virtual environment is required — everything is
bundled into the executable.

## Configuration

Key settings in `.env`:

| Variable | Description |
|---|---|
| `SECRET_KEY` | Cryptographic signing key used by Flask. **Required** in production. |
| `API_KEY` | Bearer token for API authentication. Leave empty to disable authentication (not recommended). |
| `VIBRATIONVIEW_FOLDER` | Root folder for VibrationVIEW data (e.g. `C:\VibrationVIEW`) |
| `EXE_NAME` | Full path to VibrationVIEW executable |
| `VV_CONNECTION_TIMEOUT` | COM connection timeout in seconds |
| `VV_RETRY_ATTEMPTS` | Number of connection retries |
| `CORS_ORIGINS` | Restricts browser-based cross-origin requests. Defaults to `http://127.0.0.1`, which blocks any unexpected browser-based cross-origin request while having zero impact on the controller PC or CLI tool, since server-to-server HTTP calls do not check CORS headers. Do not change back to `*`. |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## API Endpoints

Once running, access the API documentation at:

- **Docs**: `http://localhost:5000/api/v1/docs`
- **Health check**: `http://localhost:5000/api/v1/health`

## Breaking Changes

See the [CHANGELOG](https://github.com/VibrationResearch/VibrationVIEW-API-REST/blob/main/CHANGELOG.md)
for the full list of breaking changes, security updates, and improvements in each release.

## Troubleshooting

- **Server refuses to start**: `SECRET_KEY` or `API_KEY` in `.env` are still set to their default placeholder values. Generate secure values using the command in [Quick Start](#quick-start) step 2.
- **"VCRUNTIME" or DLL errors**: Install the [Microsoft Visual C++ Redistributable] (https://aka.ms/vs/17/release/vc_redist.x64.exe)
- **VibrationVIEW connection errors**: Verify VibrationVIEW is installed and the paths in `.env` are correct.
- **Port already in use**: Another process is using the default port. Choose a different port with `--port`.
- **Test fails to run**: VibrationVIEW requires system limits to be configured before running a test. Set them in VibrationVIEW via Configuration → System Limits.
