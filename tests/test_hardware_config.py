# ============================================================================
# FILE: tests/test_hardware_config.py
# ============================================================================

"""
Tests for hardware config endpoints (issue #15).

Verifies that channel parameters use 1-based indexing and convert
to 0-based internally for COM calls.
"""

import pytest

from app import create_app, reset_vv_instance, set_vv_instance
from config import TestingConfig
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


@pytest.fixture
def client():
    reset_vv_instance()
    mock_vv = MockVibrationVIEW()
    set_vv_instance(mock_vv)
    app = create_app(TestingConfig)
    with app.test_client() as c:
        yield c, mock_vv
    reset_vv_instance()


class TestHardwareSupportsChannelIndexing:
    """Hardware capability endpoints accept 1-based channels and convert to 0-based for COM."""

    @pytest.mark.parametrize(
        "endpoint,method",
        [
            ("/api/v1/hardwaresupportscapacitorcoupled", "HardwareSupportsCapacitorCoupled"),
            ("/api/v1/hardwaresupportsaccelpowersource", "HardwareSupportsAccelPowerSource"),
            ("/api/v1/hardwaresupportsdifferential", "HardwareSupportsDifferential"),
        ],
    )
    def test_channel_1_sends_0_to_com(self, client, endpoint, method):
        """User passes channel=1, COM receives channel=0."""
        c, mock_vv = client
        response = c.get(f"{endpoint}?1")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["channel"] == 1

        # Verify COM was called with 0-based index
        mock_method = getattr(mock_vv, method)
        mock_method.assert_called_once_with(0)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/hardwaresupportscapacitorcoupled",
            "/api/v1/hardwaresupportsaccelpowersource",
            "/api/v1/hardwaresupportsdifferential",
        ],
    )
    def test_channel_0_rejected(self, client, endpoint):
        """Channel 0 is invalid in 1-based indexing."""
        c, _ = client
        response = c.get(f"{endpoint}?0")
        assert response.status_code == 400

    @pytest.mark.parametrize(
        "endpoint",
        [
            "/api/v1/hardwaresupportscapacitorcoupled",
            "/api/v1/hardwaresupportsaccelpowersource",
            "/api/v1/hardwaresupportsdifferential",
        ],
    )
    def test_missing_channel_rejected(self, client, endpoint):
        """Missing channel parameter returns 400."""
        c, _ = client
        response = c.get(endpoint)
        assert response.status_code == 400
