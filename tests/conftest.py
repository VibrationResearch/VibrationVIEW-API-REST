# ============================================================================
# FILE: tests/conftest.py
# ============================================================================

"""
Pytest configuration and shared fixtures for VibrationVIEW API tests
"""

import pytest
from unittest.mock import MagicMock
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ----------------------------------------------------------------------------
# CRITICAL: Mock the vibrationviewapi module BEFORE any imports that use it
# ----------------------------------------------------------------------------
def mock_vibrationviewapi_early():
    """Mock vibrationviewapi module early to prevent real imports"""
    from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW

    mock_module = MagicMock()
    mock_module.VibrationVIEW = MockVibrationVIEW
    mock_module.MockVibrationVIEW = MockVibrationVIEW
    mock_module.get_vibrationview_instance = lambda: MockVibrationVIEW()
    mock_module.connect_to_vibrationview = lambda: MockVibrationVIEW()

    sys.modules['vibrationviewapi'] = mock_module

# Apply the mock immediately on conftest load
mock_vibrationviewapi_early()

# ----------------------------------------------------------------------------
# Safe to import app components now
# ----------------------------------------------------------------------------
try:
    from app import create_app
    from config import TestingConfig
except ImportError as e:
    print(f"Warning: Could not import app components: {e}")
    create_app = None
    TestingConfig = None

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------

@pytest.fixture
def mock_vibrationview():
    """Create a fresh mock VibrationVIEW instance for each test"""
    from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW
    mock_instance = MockVibrationVIEW()
    mock_instance.reset_mock()  # Ensure clean state
    return mock_instance

@pytest.fixture
def mock_vibrationviewapi_module(monkeypatch, mock_vibrationview):
    """Mock the vibrationviewapi module to return our specific mock instance"""

    mock_module = MagicMock()
    mock_module.VibrationVIEW = lambda *args, **kwargs: mock_vibrationview
    mock_module.VibrationVIEW.return_value = mock_vibrationview

    monkeypatch.setitem(sys.modules, 'vibrationviewapi', mock_module)
    try:
        monkeypatch.setattr('vibrationviewapi.VibrationVIEW', lambda *args, **kwargs: mock_vibrationview)
    except (ImportError, AttributeError):
        pass

    return mock_vibrationview

@pytest.fixture
def mock_vv_manager_with_api(monkeypatch, mock_vibrationview):
    """Mock any VibrationVIEW manager patterns"""

    def mock_vibrationview_class(*args, **kwargs):
        return mock_vibrationview

    def mock_with_vibrationview(func):
        def wrapper(*args, **kwargs):
            return func(mock_vibrationview, *args, **kwargs)
        wrapper.__name__ = getattr(func, '__name__', 'wrapped_function')
        return wrapper

    patch_targets = [
        ('vibrationviewapi.VibrationVIEW', mock_vibrationview_class),
        ('utils.vv_manager.VibrationVIEW', mock_vibrationview_class),
        ('utils.vv_manager.get_vv_instance', lambda *args, **kwargs: mock_vibrationview),
        ('utils.vv_manager.create_vv_instance', lambda *args, **kwargs: mock_vibrationview),
        ('utils.vv_manager.with_vibrationview', mock_with_vibrationview),
    ]

    for target, mock_obj in patch_targets:
        try:
            monkeypatch.setattr(target, mock_obj)
        except (ImportError, AttributeError):
            pass

    route_modules = [
        'routes.basic_control',
        'routes.test_control',
        'routes.status_properties',
        'routes.data_retrieval',
        'routes.hardware_config',
        'routes.gui_control',
        'routes.recording',
        'routes.reporting',
        'routes.auxinputs',
        'routes.teds',
        'routes.utility'
    ]

    for module_name in route_modules:
        try:
            monkeypatch.setattr(f'{module_name}.with_vibrationview', mock_with_vibrationview)
        except (ImportError, AttributeError):
            pass

    try:
        monkeypatch.setitem(sys.modules, 'vibrationviewapi', MagicMock())
        monkeypatch.setattr('vibrationviewapi.VibrationVIEW', mock_vibrationview_class)
    except:
        pass

    return mock_vibrationview

@pytest.fixture
def app(mock_vv_manager_with_api):
    """Create and configure a test app with mocked VibrationVIEW API"""
    if create_app is None:
        pytest.skip("Cannot create app - missing dependencies")

    # CRITICAL: Set the mock instance BEFORE create_app() because early binding
    # calls get_vv_instance() inside create_app()
    from app import set_vv_instance, reset_vv_instance
    set_vv_instance(mock_vv_manager_with_api)

    app = create_app(TestingConfig or object())
    app.config['TESTING'] = True

    yield app

    # Cleanup after test
    reset_vv_instance()

@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()

# Backward compatibility aliases
@pytest.fixture
def mock_vv_manager(mock_vv_manager_with_api):
    return mock_vv_manager_with_api

@pytest.fixture
def mock_vv_instance(mock_vibrationview):
    return mock_vibrationview
