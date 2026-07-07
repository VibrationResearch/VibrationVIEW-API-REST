# ============================================================================
# FILE: tests/test_gui_control.py
# ============================================================================

"""
Tests for GUI control route APIError cases
"""

import json

from app import get_vv_instance


class TestGuiControl:
    def test_edittest_missing_filename(self, client):
        """Test POST /edittest without filename parameter"""
        response = client.post("/api/v1/edittest")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"
