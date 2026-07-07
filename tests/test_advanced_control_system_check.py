# ============================================================================
# FILE: tests/test_advanced_control_system_check.py
# ============================================================================

"""
Tests for advanced control system check route APIError cases
"""

import json

import pytest

from app import get_vv_instance


class TestAdvancedControlSystemCheck:
    @pytest.fixture(autouse=True)
    def _setup_mock(self, client):
        self.mock_instance = get_vv_instance()

    @pytest.mark.parametrize(
        "endpoint",
        ["/api/v1/systemcheckfrequency", "/api/v1/systemcheckoutputvoltage"],
    )
    def test_post_missing_value(self, client, endpoint):
        """Test POST to system check endpoints without value parameter"""
        response = client.post(endpoint)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_systemcheckfrequency_get_success(self, client):
        """Test GET /systemcheckfrequency returns current value"""
        self.mock_instance.SystemCheckFrequency = lambda *args: 120.0 if not args else None

        response = client.get("/api/v1/systemcheckfrequency")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == 120.0
