# VibrationVIEW REST API — Setup Guide

## Prerequisites

- **Windows** machine
- **VibrationVIEW** installed on the target machine

## Quick Start

1. Extract the release zip to a folder on the target machine.
2. Copy `.env.example` to `.env` and edit it to match your environment.
   At minimum, generate secure values for `SECRET_KEY` and `API_KEY`:

   ```cmd
   powershell -Command "[Convert]::ToHexString([Security.Cryptography.RandomNumberGenerator]::GetBytes(32))"
   ```

   Copy the output into `.env` for each key. The server will refuse to start
   in production mode if `SECRET_KEY` is still the development default or if
   `API_KEY` is still the placeholder value.

3. Run the executable:

```cmd
VibrationVIEW-API.exe
VibrationVIEW-API.exe --port 8080
VibrationVIEW-API.exe --debug
VibrationVIEW-API.exe --host 0.0.0.0 --port 5000 --threads 8
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

- **UTC timestamps**: All API response timestamps now use UTC with an explicit
  `+00:00` offset (e.g., `2026-06-19T18:30:00+00:00`). Previously, timestamps
  used local time without a timezone indicator. Update any client-side parsing
  that assumes local time.

## Troubleshooting

- **"VCRUNTIME" or DLL errors**: Install the
  [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)
  for your platform.
- **VibrationVIEW connection errors**: Verify VibrationVIEW is installed and
  the paths in `.env` are correct.
- **Port already in use**: Another process is using the default port. Choose a
  different port with `--port`.
