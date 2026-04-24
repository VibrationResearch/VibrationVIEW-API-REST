@echo off
REM ============================================================================
REM setup.bat - Offline setup of VibrationVIEW REST API
REM Creates a virtual environment and installs all dependencies from the
REM local vendor\ folder. No internet access required.
REM
REM Prerequisites:
REM   - Python 3.x installed and on PATH
REM   - vendor\ folder populated by prepare-offline.ps1
REM
REM Usage:
REM   setup.bat                          defaults
REM   setup.bat --venv .venv             custom venv path
REM   setup.bat --start                  set up and start the server
REM ============================================================================

setlocal enabledelayedexpansion

set "VENV_DIR=venv"
set "PACKAGE_DIR=vendor"
set "START_SERVER=0"

REM --- Parse arguments --------------------------------------------------------
:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--venv" (
    set "VENV_DIR=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--packages" (
    set "PACKAGE_DIR=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--start" (
    set "START_SERVER=1"
    shift
    goto parse_args
)
echo Unknown argument: %~1
exit /b 1
:done_args

REM --- Pre-flight checks ------------------------------------------------------
echo.
echo ^>^> Checking prerequisites

REM Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo    Python not found on PATH. Install Python 3.x and try again.
    exit /b 1
)
for /f "delims=" %%v in ('python --version 2^>^&1') do set "PY_VERSION=%%v"
echo    Found %PY_VERSION%

REM Vendor directory
if not exist "%PACKAGE_DIR%\" (
    echo    Vendor directory '%PACKAGE_DIR%' not found.
    echo    Run prepare-offline.ps1 on a machine with internet first.
    exit /b 1
)
set "PKG_COUNT=0"
for %%f in ("%PACKAGE_DIR%\*.*") do set /a PKG_COUNT+=1
if %PKG_COUNT% equ 0 (
    echo    Vendor directory is empty. Re-run prepare-offline.ps1.
    exit /b 1
)
echo    Found %PKG_COUNT% packages in %PACKAGE_DIR%

REM --- Create virtual environment ---------------------------------------------
echo.
echo ^>^> Creating virtual environment at %VENV_DIR%

if exist "%VENV_DIR%\" (
    echo    Removing existing venv ...
    rmdir /s /q "%VENV_DIR%"
)

python -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo    Failed to create virtual environment.
    exit /b 1
)
echo    Virtual environment created

REM --- Install dependencies ---------------------------------------------------
echo.
echo ^>^> Installing dependencies from %PACKAGE_DIR% (offline)

set "PIP_EXE=%VENV_DIR%\Scripts\pip.exe"

REM Upgrade pip from vendor if a newer pip wheel is present
if exist "%PACKAGE_DIR%\pip-*.whl" (
    "%PIP_EXE%" install --no-index --find-links "%PACKAGE_DIR%" --upgrade pip >nul 2>&1
)

REM Install all requirements offline
"%PIP_EXE%" install --no-index --find-links "%PACKAGE_DIR%" -r requirements.txt
if %errorlevel% neq 0 (
    echo    Package installation failed.
    echo    Ensure prepare-offline.ps1 was run with the same Python version and platform.
    exit /b 1
)
echo    All packages installed

REM --- Copy .env if needed ----------------------------------------------------
if not exist ".env" (
    if exist ".env.example" (
        echo.
        echo ^>^> Creating .env from .env.example
        copy ".env.example" ".env" >nul
        echo    .env created - edit it to match your environment
    )
)

REM --- Summary ----------------------------------------------------------------
echo.
echo ============================================
echo   Setup complete!
echo ============================================
echo.
echo To activate the virtual environment:
echo   %VENV_DIR%\Scripts\activate.bat
echo.
echo To start the server:
echo   python app.py --host 127.0.0.1 --port 5000
echo.

REM --- Optionally start the server --------------------------------------------
if %START_SERVER% equ 1 (
    echo ^>^> Starting VibrationVIEW REST API server
    call "%VENV_DIR%\Scripts\activate.bat"
    python app.py --host 127.0.0.1 --port 5000
)

endlocal
