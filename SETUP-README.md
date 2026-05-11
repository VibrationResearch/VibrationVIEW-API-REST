# VibrationVIEW REST API — Offline Setup Guide

## Prerequisites

- **Windows** with Python 3.x installed and on PATH
- **VibrationVIEW** installed on the target machine

## Quick Start

1. Extract the zip file to a folder on the target machine.
2. Run the setup script (choose one):

**Option A: Using the batch file (Command Prompt)**

```cmd
setup.bat
```

**Option B: Using PowerShell**

```powershell
.\setup.ps1
```

Both scripts create a virtual environment and install all dependencies from the
bundled `vendor/` folder. No internet access is required. A `.env` file is
created automatically from `.env.example` if one does not already exist.

3. Edit `.env` to match your environment (paths, connection settings, etc.).
4. Start the server:

**Option A: Using the batch file**

```cmd
start-api.bat
start-api.bat --port 8080
start-api.bat --debug
```

**Option B: Using PowerShell**

```powershell
.\venv\Scripts\Activate.ps1
python app.py --host 127.0.0.1 --port 5000
```

**Setup and start in one step:**

```cmd
setup.bat --start
```

```powershell
.\setup.ps1 -Start
```

## Configuration

Key settings in `.env`:

| Variable | Description |
|---|---|
| `VIBRATIONVIEW_FOLDER` | Root folder for VibrationVIEW data (e.g. `C:\VibrationVIEW`) |
| `EXE_NAME` | Full path to VibrationVIEW executable |
| `VV_CONNECTION_TIMEOUT` | COM connection timeout in seconds |
| `VV_RETRY_ATTEMPTS` | Number of connection retries |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## API Endpoints

Once running, access the API documentation at:

- **Docs**: `http://localhost:5000/api/v1/docs`
- **Health check**: `http://localhost:5000/api/v1/health`

## Troubleshooting

- **"Python not found"**: Ensure Python 3.x is installed and added to PATH.
- **Package installation fails**: The vendor packages were built for a specific
  Python version and platform. Re-run `prepare-offline.ps1` on a machine with
  the same Python version and Windows architecture as the target.
- **VibrationVIEW connection errors**: Verify VibrationVIEW is installed and
  the paths in `.env` are correct.
