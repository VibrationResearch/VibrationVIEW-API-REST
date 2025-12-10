# ============================================================================
# FILE: tests/test_input_config.py
# ============================================================================

"""
Tests for input configuration routes
"""

import json
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestInputConfig:
    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    # -------------------------------------------------------------------------
    # InputMode tests - JSON body
    # -------------------------------------------------------------------------
    def test_inputmode_json_success(self, client):
        """Test POST /inputmode with JSON body"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is True

        # Verify the COM method was called with correct parameters
        # Channel 1 (user) -> Channel 0 (COM, 0-based)
        self.mock_instance.InputMode.assert_called_once_with(0, True, False, True)

    def test_inputmode_channel_conversion(self, client):
        """Test that channel numbers are converted from 1-based to 0-based"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 4,
                "powersource": False,
                "capcoupled": True,
                "differential": False
            }
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["channel"] == 4

        # Verify COM method called with 0-based index (channel 4 -> index 3)
        self.mock_instance.InputMode.assert_called_once_with(3, False, True, False)

    # -------------------------------------------------------------------------
    # InputMode tests - Query parameters
    # -------------------------------------------------------------------------
    def test_inputmode_query_params_get(self, client):
        """Test GET /inputmode with query parameters"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=true&capcoupled=false&differential=false"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["result"] is True
        assert data["data"]["channel"] == 1
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is False

        # Verify the COM method was called with correct parameters
        self.mock_instance.InputMode.assert_called_once_with(0, True, False, False)

    def test_inputmode_query_params_post(self, client):
        """Test POST /inputmode with query parameters"""
        response = client.post(
            "/api/v1/inputmode?channel=2&powersource=false&capcoupled=true&differential=true"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["channel"] == 2
        assert data["data"]["powersource"] is False
        assert data["data"]["capcoupled"] is True
        assert data["data"]["differential"] is True

        # Verify COM method called with 0-based index (channel 2 -> index 1)
        self.mock_instance.InputMode.assert_called_once_with(1, False, True, True)

    def test_inputmode_query_params_all_false(self, client):
        """Test GET /inputmode with all boolean parameters as false strings"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=false&capcoupled=false&differential=false"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["powersource"] is False
        assert data["data"]["capcoupled"] is False
        assert data["data"]["differential"] is False

        self.mock_instance.InputMode.assert_called_once_with(0, False, False, False)

    def test_inputmode_query_params_all_true(self, client):
        """Test GET /inputmode with all boolean parameters as true strings"""
        response = client.get(
            "/api/v1/inputmode?channel=1&powersource=true&capcoupled=true&differential=true"
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["powersource"] is True
        assert data["data"]["capcoupled"] is True
        assert data["data"]["differential"] is True

        self.mock_instance.InputMode.assert_called_once_with(0, True, True, True)

    # -------------------------------------------------------------------------
    # InputMode tests - Error cases
    # -------------------------------------------------------------------------
    def test_inputmode_missing_channel(self, client):
        """Test POST /inputmode without channel parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "channel" in data["error"]["message"].lower()

    def test_inputmode_missing_powersource(self, client):
        """Test POST /inputmode without powersource parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "powersource" in data["error"]["message"].lower()

    def test_inputmode_missing_capcoupled(self, client):
        """Test POST /inputmode without capcoupled parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "capcoupled" in data["error"]["message"].lower()

    def test_inputmode_missing_differential(self, client):
        """Test POST /inputmode without differential parameter"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 1,
                "powersource": True,
                "capcoupled": False
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "differential" in data["error"]["message"].lower()

    def test_inputmode_missing_params(self, client):
        """Test POST /inputmode without any parameters"""
        response = client.post("/api/v1/inputmode")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "missing" in data["error"]["message"].lower()

    def test_inputmode_invalid_channel_zero(self, client):
        """Test POST /inputmode with channel 0 (invalid, 1-based)"""
        response = client.post(
            "/api/v1/inputmode",
            json={
                "channel": 0,
                "powersource": True,
                "capcoupled": False,
                "differential": True
            }
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_inputmode_query_params_missing_channel(self, client):
        """Test GET /inputmode with missing channel in query params"""
        response = client.get(
            "/api/v1/inputmode?powersource=true&capcoupled=false&differential=false"
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "channel" in data["error"]["message"].lower()
