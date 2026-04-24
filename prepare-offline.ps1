# ============================================================================
# prepare-offline.ps1 — Download all dependencies and create a deployment zip
# Run this on a machine WITH internet access. The resulting zip file can be
# copied to an offline machine and extracted to set up the application.
# ============================================================================

param(
    [string]$PackageDir = ".\vendor",
    [string]$ZipName    = "VibrationVIEW-API.zip"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Preparing offline deployment package ===" -ForegroundColor Cyan

# --- Step 1: Download packages ---------------------------------------------
Write-Host ""
Write-Host "[1/3] Downloading packages" -ForegroundColor Cyan

if (Test-Path $PackageDir) {
    Write-Host "  Cleaning existing $PackageDir ..."
    Remove-Item -Recurse -Force $PackageDir
}
New-Item -ItemType Directory -Path $PackageDir | Out-Null

Write-Host "  Downloading from requirements.txt ..." -ForegroundColor Yellow
pip download -r requirements.txt -d $PackageDir --only-binary :all:
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Some packages have no wheel; retrying allowing sdists ..." -ForegroundColor Yellow
    pip download -r requirements.txt -d $PackageDir
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to download packages." -ForegroundColor Red
    exit 1
}

$count = (Get-ChildItem $PackageDir -File).Count
Write-Host "  $count packages downloaded" -ForegroundColor Green

# --- Step 2: Stage files into a temp directory ------------------------------
Write-Host ""
Write-Host "[2/3] Staging deployment files" -ForegroundColor Cyan

$stagingDir = Join-Path $env:TEMP "vvapi-staging-$(Get-Random)"
New-Item -ItemType Directory -Path $stagingDir | Out-Null

# Application source
$appFiles = @(
    "app.py",
    "config.py",
    "requirements.txt",
    ".env.example",
    "setup.ps1",
    "setup.bat",
    "start-api.bat",
    "SETUP-README.md"
)

foreach ($file in $appFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $stagingDir
        Write-Host "  + $file"
    }
}

# Directories
$appDirs = @("routes", "utils", "templates")
foreach ($dir in $appDirs) {
    if (Test-Path $dir) {
        Copy-Item $dir -Destination (Join-Path $stagingDir $dir) -Recurse
        Write-Host "  + $dir/"
    }
}

# Vendor packages
Copy-Item $PackageDir -Destination (Join-Path $stagingDir "vendor") -Recurse
Write-Host "  + vendor/ ($count packages)"

# --- Step 3: Create zip ----------------------------------------------------
Write-Host ""
Write-Host "[3/3] Creating $ZipName" -ForegroundColor Cyan

$zipPath = Join-Path (Get-Location) $ZipName
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

Compress-Archive -Path "$stagingDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Clean up staging
Remove-Item -Recurse -Force $stagingDir

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  Deployment package created!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  File: $ZipName ($sizeMB MB)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Contents:" -ForegroundColor Yellow
Write-Host "    - Application source (app.py, routes/, utils/, templates/)"
Write-Host "    - setup.ps1 / setup.bat (offline installer)"
Write-Host "    - start-api.bat (launch shortcut)"
Write-Host "    - SETUP-README.md (setup instructions)"
Write-Host "    - .env.example (configuration template)"
Write-Host "    - vendor/ ($count pre-downloaded packages)"
Write-Host ""
Write-Host "  To deploy on an offline machine:" -ForegroundColor Yellow
Write-Host "    1. Extract the zip"
Write-Host "    2. Run: setup.bat"
Write-Host ""
