# ============================================================================
# FILE: tests/test_virtual_channels.py
# ============================================================================

"""
Tests for virtual channels route APIError cases
"""

import json

from app import get_vv_instance


class TestVirtualChannels:
    def test_importvirtualchannels_missing_filename(self, client):
        """Test POST /importvirtualchannels without filename parameter"""
        response = client.post("/api/v1/importvirtualchannels")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "MISSING_PARAMETER"
