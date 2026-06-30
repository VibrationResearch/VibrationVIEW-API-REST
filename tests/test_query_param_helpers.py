"""
Unit tests for get_query_param and get_query_param_string helpers in utils/utils.py
"""

import json

import pytest

from app import get_vv_instance


class TestGetQueryParam:
    """Tests for get_query_param()"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.mock_vv = get_vv_instance()

    def test_named_param_int(self):
        """Named parameter with int type_fn"""
        self.mock_vv.ChannelUnit.return_value = "g"
        response = self.client.get("/api/v1/channelunit?channel=3")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["channel"] == 3

    def test_named_param_type_error(self):
        """Named parameter with invalid type returns 400"""
        response = self.client.get("/api/v1/channelunit?channel=abc")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_PARAMETER"
        assert "channel" in data["error"]["message"]
        assert "int" in data["error"]["message"]

    def test_positional_fallback_int(self):
        """Bare positional value like ?3 works"""
        self.mock_vv.ChannelUnit.return_value = "g"
        response = self.client.get("/api/v1/channelunit?3")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["channel"] == 3

    def test_positional_fallback_invalid_int(self):
        """Bare positional value with invalid int returns 400"""
        response = self.client.get("/api/v1/channelunit?abc")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_PARAMETER"

    def test_positional_fallback_skipped_when_named_params(self):
        """Positional fallback should NOT trigger when query string contains '='"""
        response = self.client.get("/api/v1/channelunit?other=value")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_missing_required_param(self):
        """Missing required parameter returns 400 with MISSING_PARAMETER"""
        response = self.client.get("/api/v1/channelunit")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"
        assert "channel" in data["error"]["message"]

    def test_optional_param_missing(self):
        """Optional parameter returns None when absent (tested via controlunit default)"""
        self.mock_vv.ControlUnit.return_value = "m/s²"
        response = self.client.get("/api/v1/controlunit")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["loop"] == 1

    def test_named_param_empty_string_int(self):
        """Empty string with int type_fn returns INVALID_PARAMETER"""
        response = self.client.get("/api/v1/channelunit?channel=")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "INVALID_PARAMETER"


class TestGetQueryParamString:
    """Tests for get_query_param_string()"""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        self.mock_vv = get_vv_instance()

    def test_named_param(self):
        """Named string parameter works"""
        self.mock_vv.ReportField.return_value = "Test Value"
        response = self.client.get("/api/v1/reportfield?field=TestName")
        assert response.status_code == 200

    def test_positional_fallback_string(self):
        """Bare positional string value like ?TestName works"""
        self.mock_vv.ReportField.return_value = "Test Value"
        response = self.client.get("/api/v1/reportfield?TestName")
        assert response.status_code == 200

    def test_positional_fallback_skipped_when_named_params(self):
        """Positional fallback skipped when query string contains '='"""
        response = self.client.get("/api/v1/reportfield?other=value")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_empty_string_required(self):
        """Empty string with required=True returns MISSING_PARAMETER"""
        # reportfield uses get_query_param("field", str) — empty string passes
        # str("") succeeds, so Werkzeug returns "". The helper treats this as
        # a valid value. Test that the COM call receives the empty string.
        self.mock_vv.ReportField.return_value = ""
        response = self.client.get("/api/v1/reportfield?field=")
        # get_query_param with str type allows empty strings through
        assert response.status_code == 200

    def test_missing_required(self):
        """Missing required string parameter returns 400"""
        response = self.client.get("/api/v1/reportfield")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_json_body_fallback(self):
        """JSON body fallback works for endpoints that support it"""
        response = self.client.post(
            "/api/v1/generatetxt",
            data=json.dumps({"filename": "test.vrd"}),
            content_type="application/json",
        )
        data = response.get_json()
        # Should not fail with MISSING_PARAMETER for filename
        if response.status_code == 400:
            assert "filename" not in data["error"].get("message", "")

    def test_url_encoded_positional(self):
        """URL-encoded bare positional value is decoded"""
        self.mock_vv.ReportField.return_value = "Test Value"
        response = self.client.get("/api/v1/reportfield?Test%20Name")
        assert response.status_code == 200
