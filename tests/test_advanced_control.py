# ============================================================================
# FILE: tests/test_advanced_control.py
# ============================================================================

"""
Tests for advanced control route APIError cases
"""

import json

from app import get_vv_instance


class TestAdvancedControl:
    def test_testtype_post_missing_value(self, client):
        """Test POST /testtype without value parameter"""
        response = client.post("/api/v1/testtype")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_testtype_get_success(self, client):
        """Test GET /testtype returns current value"""
        mock_instance = get_vv_instance()
        mock_instance.TestType = lambda *args: 1 if not args else None

        response = client.get("/api/v1/testtype")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] == 1
