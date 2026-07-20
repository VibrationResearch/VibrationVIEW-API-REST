# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec for VibrationVIEW REST API.

Build:
    pyinstaller app.spec

Output:
    dist/VibrationVIEW-API/  (one-folder bundle)
"""

import os
import sys

block_cipher = None

# Hidden imports that PyInstaller cannot detect via static analysis
hidden_imports = [
    # Flask and extensions
    "flask",
    "flask.json",
    "flask.json.provider",
    "flask_cors",
    "jinja2",
    "markupsafe",
    # WSGI server
    "waitress",
    "waitress.server",
    "waitress.task",
    "waitress.channel",
    "waitress.adjustments",
    # Environment
    "dotenv",
    "dotenv.main",
    # Windows COM
    "win32com",
    "win32com.client",
    "win32api",
    "win32con",
    "pythoncom",
    "pywintypes",
    # VibrationVIEW
    "vibrationviewapi",
    # Application modules — routes
    "routes",
    "routes.advanced_control",
    "routes.advanced_control_sine",
    "routes.advanced_control_system_check",
    "routes.aux_inputs",
    "routes.basic_control",
    "routes.data_retrieval",
    "routes.gui_control",
    "routes.hardware_config",
    "routes.input_config",
    "routes.log",
    "routes.recording",
    "routes.report_generation",
    "routes.reporting",
    "routes.status_properties",
    "routes.teds",
    "routes.vectors_legacy",
    "routes.virtual_channels",
    # Application modules — utils
    "utils",
    "utils.decorators",
    "utils.exceptions",
    "utils.path_validator",
    "utils.response_helpers",
    "utils.teds_formatter",
    "utils.utils",
    "utils.vv_error_codes",
    "utils.vv_manager",
    "utils.vv_singleton",
    "utils.write_guard",
    # Config
    "config",
]

a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=[
        (".env.example", "."),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test-only packages
        "pytest",
        "coverage",
        "faker",
        "mypy",
        "ruff",
        # Unused stdlib modules
        "tkinter",
        "unittest",
    ],
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VibrationVIEW-API",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="VibrationVIEW-API",
)
