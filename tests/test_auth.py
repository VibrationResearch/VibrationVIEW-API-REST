# ============================================================================
# FILE: tests/test_auth.py
# ============================================================================

"""
Tests for API key authentication and public endpoint exemptions.
"""

import pytest

from app import create_app, reset_vv_instance, set_vv_instance
from config import TestingConfig


class AuthTestConfig(TestingConfig):
    """Testing config with API key enabled"""
    API_KEY = 'test-api-key-12345'


@pytest.fixture
def auth_app(mock_vv_manager_with_api):
    """Create app with API key authentication enabled"""
    set_vv_instance(mock_vv_manager_with_api)
    app = create_app(AuthTestConfig)
    yield app
    reset_vv_instance()


@pytest.fixture
def auth_client(auth_app):
    """Test client for app with auth enabled"""
    return auth_app.test_client()


class TestPublicEndpoints:
    """Test that health and docs endpoints work without authentication"""

    def test_health_no_auth(self, auth_client):
        """GET /api/v1/health should be accessible without API key"""
        response = auth_client.get('/api/v1/health')
        assert response.status_code == 200

    def test_docs_no_auth(self, auth_client):
        """GET /api/v1/docs should be accessible without API key"""
        response = auth_client.get('/api/v1/docs')
        assert response.status_code == 200

    def test_docs_module_no_auth(self, auth_client):
        """GET /api/v1/docs/advanced_control_sine should be accessible without API key"""
        response = auth_client.get('/api/v1/docs/advanced_control_sine')
        assert response.status_code == 200


class TestProtectedEndpoints:
    """Test that other endpoints require authentication"""

    def test_protected_endpoint_no_auth(self, auth_client):
        """Protected endpoint should return 401 without API key"""
        response = auth_client.get('/api/v1/isready')
        assert response.status_code == 401

    def test_protected_endpoint_wrong_key(self, auth_client):
        """Protected endpoint should return 401 with wrong API key"""
        response = auth_client.get('/api/v1/isready',
                                   headers={'Authorization': 'Bearer wrong-key'})
        assert response.status_code == 401

    def test_protected_endpoint_valid_key(self, auth_client):
        """Protected endpoint should return 200 with valid API key"""
        response = auth_client.get('/api/v1/isready',
                                   headers={'Authorization': 'Bearer test-api-key-12345'})
        assert response.status_code == 200
