# ============================================================================
# setup.ps1 - Offline setup of VibrationVIEW REST API
# Creates a virtual environment and installs all dependencies from the
# local vendor/ folder. No internet access required.
#
# Prerequisites:
#   - Python 3.x installed and on PATH
#   - vendor/ folder populated by prepare-offline.ps1
#
# Usage:
#   .\setup.ps1                        # defaults
#   .\setup.ps1 -VenvDir ".venv"       # custom venv path
#   .\setup.ps1 -Start                 # set up and start the server
# ============================================================================

param(
    [string]$VenvDir    = ".\venv",
    [string]$PackageDir = ".\vendor",
    [switch]$Start
)

$ErrorActionPreference = "Stop"

# --- Helpers ----------------------------------------------------------------
function Write-Step($msg) { Write-Host "`n>> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "   $msg"   -ForegroundColor Green }
function Write-Err($msg)  { Write-Host "   $msg"   -ForegroundColor Red }

# --- Pre-flight checks ------------------------------------------------------
Write-Step "Checking prerequisites"

# Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Err "Python not found on PATH. Install Python 3.x and try again."
    exit 1
}
$pyVersion = & python --version 2>&1
Write-Ok "Found $pyVersion"

# Vendor directory
if (-not (Test-Path $PackageDir)) {
    Write-Err "Vendor directory '$PackageDir' not found."
    Write-Err "Run prepare-offline.ps1 on a machine with internet first."
    exit 1
}
$pkgCount = (Get-ChildItem $PackageDir -File).Count
if ($pkgCount -eq 0) {
    Write-Err "Vendor directory is empty. Re-run prepare-offline.ps1."
    exit 1
}
Write-Ok "Found $pkgCount packages in $PackageDir"

# --- Create virtual environment ---------------------------------------------
Write-Step "Creating virtual environment at $VenvDir"

if (Test-Path $VenvDir) {
    Write-Host "   Removing existing venv ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $VenvDir
}

python -m venv $VenvDir
if ($LASTEXITCODE -ne 0) {
    Write-Err "Failed to create virtual environment."
    exit 1
}
Write-Ok "Virtual environment created"

# --- Activate and install ---------------------------------------------------
Write-Step "Installing dependencies from $PackageDir (offline)"

$pipExe = Join-Path $VenvDir "Scripts\pip.exe"

# Upgrade pip from vendor if a newer pip wheel is present
$pipWheel = Get-ChildItem $PackageDir -Filter "pip-*.whl" | Select-Object -First 1
if ($pipWheel) {
    & $pipExe install --no-index --find-links $PackageDir --upgrade pip 2>$null
}

# Install all requirements offline
& $pipExe install --no-index --find-links $PackageDir -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Err "Package installation failed."
    Write-Err "Ensure prepare-offline.ps1 was run with the same Python version and platform."
    exit 1
}
Write-Ok "All packages installed"

# --- Copy .env if needed ----------------------------------------------------
if (-not (Test-Path ".\.env")) {
    if (Test-Path ".\.env.example") {
        Write-Step "Creating .env from .env.example"
        Copy-Item ".\.env.example" ".\.env"
        Write-Ok ".env created - edit it to match your environment"
    }
}

# --- Summary ----------------------------------------------------------------
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment:"
Write-Host "  $VenvDir\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start the server:"
Write-Host "  python app.py --host 127.0.0.1 --port 5000" -ForegroundColor Yellow
Write-Host ""

# --- Optionally start the server -------------------------------------------
if ($Start) {
    Write-Step "Starting VibrationVIEW REST API server"
    & "$VenvDir\Scripts\Activate.ps1"
    & python app.py --host 127.0.0.1 --port 5000
}
