# ============================================================================
# FILE: tests/test_aux_inputs.py
# ============================================================================

"""
Tests for aux inputs route APIError cases
"""

import json

import pytest

from app import get_vv_instance


class TestAuxInputs:
    @pytest.fixture(autouse=True)
    def _setup_mock(self, client):
        self.mock_instance = get_vv_instance()

    @pytest.mark.parametrize("endpoint", ["/api/v1/rearinputunit", "/api/v1/rearinputlabel"])
    def test_missing_channel(self, client, endpoint):
        """Test GET aux input endpoints without channel parameter"""
        response = client.get(endpoint)

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"

    @pytest.mark.parametrize("endpoint", ["/api/v1/rearinputunit", "/api/v1/rearinputlabel"])
    def test_channel_zero_rejected(self, client, endpoint):
        """Test that channel 0 is rejected (1-based indexing)"""
        response = client.get(f"{endpoint}?channel=0")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_PARAMETER"
