# ============================================================================
# FILE: tests/test_write_guard.py
# ============================================================================

"""
Tests for the write guard: when ALLOW_GET_WRITE=false, GET requests to
state-changing endpoints must return 405, while POST still works.
"""

import pytest

from app import create_app, reset_vv_instance, set_vv_instance
from config import TestingConfig
from utils.write_guard import WRITE_ENDPOINTS


class WriteGuardDisabledConfig(TestingConfig):
    """Config with ALLOW_GET_WRITE disabled."""
    ALLOW_GET_WRITE = False


@pytest.fixture
def guarded_app(mock_vv_manager_with_api):
    """App instance with ALLOW_GET_WRITE=false."""
    set_vv_instance(mock_vv_manager_with_api)
    app = create_app(WriteGuardDisabledConfig)
    app.config['TESTING'] = True
    yield app
    reset_vv_instance()


@pytest.fixture
def guarded_client(guarded_app):
    """Test client with ALLOW_GET_WRITE=false."""
    return guarded_app.test_client()


@pytest.fixture
def unguarded_client(mock_vv_manager_with_api):
    """Test client with ALLOW_GET_WRITE=true (default)."""
    set_vv_instance(mock_vv_manager_with_api)
    app = create_app(TestingConfig)
    app.config['TESTING'] = True
    yield app.test_client()
    reset_vv_instance()


class TestWriteGuardBlocks:
    """GET on every write endpoint must return 405 when guard is active."""

    @pytest.mark.parametrize('endpoint', sorted(WRITE_ENDPOINTS))
    def test_get_blocked(self, guarded_client, endpoint):
        response = guarded_client.get(f'/api/v1/{endpoint}')
        assert response.status_code == 405, (
            f'GET /api/v1/{endpoint} should be 405, got {response.status_code}'
        )
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'Method not allowed'

    @pytest.mark.parametrize('endpoint', sorted(WRITE_ENDPOINTS))
    def test_post_allowed(self, guarded_client, endpoint):
        response = guarded_client.post(f'/api/v1/{endpoint}')
        assert response.status_code != 405, (
            f'POST /api/v1/{endpoint} should not be 405, got {response.status_code}'
        )


class TestWriteGuardPermits:
    """GET on write endpoints must work when guard is off."""

    @pytest.mark.parametrize('endpoint', sorted(WRITE_ENDPOINTS))
    def test_get_allowed(self, unguarded_client, endpoint):
        response = unguarded_client.get(f'/api/v1/{endpoint}')
        assert response.status_code != 405, (
            f'GET /api/v1/{endpoint} should not be 405 with guard off, got {response.status_code}'
        )


class TestReadEndpointsUnaffected:
    """Every GET endpoint not in WRITE_ENDPOINTS must remain accessible."""

    def test_get_not_blocked(self, guarded_app, guarded_client):
        """Discover all GET endpoints not in the guard and verify none return 405."""
        prefix = '/api/v1/'
        blocked = {f'{prefix}{ep}' for ep in WRITE_ENDPOINTS}
        for rule in sorted(guarded_app.url_map.iter_rules(), key=lambda r: r.rule):
            if 'GET' in rule.methods and rule.rule.startswith(prefix):
                if rule.rule not in blocked:
                    response = guarded_client.get(rule.rule)
                    assert response.status_code != 405, (
                        f'GET {rule.rule} should not be 405, got {response.status_code}'
                    )
