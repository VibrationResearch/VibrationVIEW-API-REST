@echo off
REM ============================================================================
REM start.bat - Start VibrationVIEW REST API in the virtual environment
REM
REM Usage:
REM   start.bat                          defaults (venv, port 5000)
REM   start.bat --venv .venv             custom venv path
REM   start.bat --port 8080             custom port
REM   start.bat --debug                  enable debug mode
REM ============================================================================

setlocal enabledelayedexpansion

set "VENV_DIR=venv"
set "HOST=127.0.0.1"
set "PORT=5000"
set "DEBUG="

REM --- Parse arguments --------------------------------------------------------
:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--venv" (
    set "VENV_DIR=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--host" (
    set "HOST=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--port" (
    set "PORT=%~2"
    shift
    shift
    goto parse_args
)
if /i "%~1"=="--debug" (
    set "DEBUG=--debug"
    shift
    goto parse_args
)
echo Unknown argument: %~1
exit /b 1
:done_args

REM --- Check virtual environment exists ---------------------------------------
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Virtual environment not found at '%VENV_DIR%'.
    echo Run setup.bat first to create it.
    exit /b 1
)

REM --- Activate and start -----------------------------------------------------
call "%VENV_DIR%\Scripts\activate.bat"
echo Starting VibrationVIEW REST API on %HOST%:%PORT% ...
python app.py --host %HOST% --port %PORT% %DEBUG%

endlocal
