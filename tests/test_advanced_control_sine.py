# ============================================================================
# FILE: tests/test_advanced_control_sine.py
# ============================================================================

"""
Tests for advanced control sine route APIError cases
"""

import json

import pytest

from app import get_vv_instance


class TestAdvancedControlSine:
    @pytest.fixture(autouse=True)
    def _setup_mock(self, client):
        self.mock_instance = get_vv_instance()

    @pytest.mark.parametrize(
        "endpoint",
        ["/api/v1/demandmultiplier", "/api/v1/sweepmultiplier", "/api/v1/sinefrequency"],
    )
    def test_post_missing_value(self, client, endpoint):
        """Test POST to sine parameter endpoints without value parameter"""
        response = client.post(endpoint)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_demandmultiplier_get_success(self, client):
        """Test GET /demandmultiplier returns current value"""
        self.mock_instance.DemandMultiplier = lambda *args: 6.0 if not args else None

        response = client.get("/api/v1/demandmultiplier")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == 6.0
