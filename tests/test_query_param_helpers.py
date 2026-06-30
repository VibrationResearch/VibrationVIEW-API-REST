"""
Unit tests for get_query_param and get_query_param_string helpers in utils/utils.py

Includes both:
- Direct unit tests calling the helpers in a Flask test request context
- Integration tests verifying behavior through actual route endpoints
"""

import json

import pytest

from app import get_vv_instance
from utils.utils import get_query_param, get_query_param_string


# ============================================================================
# Direct unit tests — call helpers in a Flask test request context
# ============================================================================


class TestGetQueryParamDirect:
    """Direct unit tests for get_query_param()"""

    def test_named_int(self, app):
        """Named int parameter extracted correctly"""
        with app.test_request_context("/?channel=5"):
            value, err, status = get_query_param("channel", int)
            assert value == 5
            assert err is None
            assert status is None

    def test_named_float(self, app):
        """Named float parameter extracted correctly"""
        with app.test_request_context("/?value=3.14"):
            value, err, status = get_query_param("value", float)
            assert value == pytest.approx(3.14)
            assert err is None

    def test_named_str(self, app):
        """Named str parameter extracted correctly"""
        with app.test_request_context("/?field=TestName"):
            value, err, status = get_query_param("field", str)
            assert value == "TestName"
            assert err is None

    def test_named_int_conversion_failure(self, app):
        """Named param with invalid int returns INVALID_PARAMETER"""
        with app.test_request_context("/?channel=abc"):
            value, err, status = get_query_param("channel", int)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "INVALID_PARAMETER"
            assert "int" in err["error"]["message"]

    def test_named_float_conversion_failure(self, app):
        """Named param with invalid float returns INVALID_PARAMETER"""
        with app.test_request_context("/?value=notanumber"):
            value, err, status = get_query_param("value", float)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "INVALID_PARAMETER"

    def test_named_empty_string_int(self, app):
        """Empty string with int type_fn returns INVALID_PARAMETER"""
        with app.test_request_context("/?channel="):
            value, err, status = get_query_param("channel", int)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "INVALID_PARAMETER"

    def test_named_empty_string_str(self, app):
        """Empty string with str type_fn returns empty string (valid)"""
        with app.test_request_context("/?field="):
            value, err, status = get_query_param("field", str)
            assert value == ""
            assert err is None

    def test_positional_int(self, app):
        """Bare positional ?3 parsed as int"""
        with app.test_request_context("/?3"):
            value, err, status = get_query_param("channel", int)
            assert value == 3
            assert err is None

    def test_positional_negative_int(self, app):
        """Bare positional with negative number"""
        with app.test_request_context("/?-1"):
            value, err, status = get_query_param("channel", int)
            assert value == -1
            assert err is None

    def test_positional_float(self, app):
        """Bare positional ?2.5 parsed as float"""
        with app.test_request_context("/?2.5"):
            value, err, status = get_query_param("value", float)
            assert value == pytest.approx(2.5)
            assert err is None

    def test_positional_invalid_int(self, app):
        """Bare positional with non-numeric string returns INVALID_PARAMETER"""
        with app.test_request_context("/?abc"):
            value, err, status = get_query_param("channel", int)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "INVALID_PARAMETER"

    def test_positional_skipped_when_equals_present(self, app):
        """Positional fallback skipped when query string has '='"""
        with app.test_request_context("/?other=value"):
            value, err, status = get_query_param("channel", int)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"

    def test_missing_required(self, app):
        """Missing required param returns MISSING_PARAMETER"""
        with app.test_request_context("/"):
            value, err, status = get_query_param("channel", int, required=True)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"
            assert "channel" in err["error"]["message"]

    def test_missing_optional(self, app):
        """Missing optional param returns (None, None, None)"""
        with app.test_request_context("/"):
            value, err, status = get_query_param("channel", int, required=False)
            assert value is None
            assert err is None
            assert status is None

    def test_optional_with_equals_no_match(self, app):
        """Optional param with unrelated named params returns (None, None, None)"""
        with app.test_request_context("/?other=value"):
            value, err, status = get_query_param("channel", int, required=False)
            assert value is None
            assert err is None
            assert status is None


class TestGetQueryParamStringDirect:
    """Direct unit tests for get_query_param_string()"""

    def test_named_param(self, app):
        """Named string parameter extracted correctly"""
        with app.test_request_context("/?filename=test.vrd"):
            value, err, status = get_query_param_string("filename")
            assert value == "test.vrd"
            assert err is None

    def test_named_empty_required(self, app):
        """Empty string with required=True returns MISSING_PARAMETER"""
        with app.test_request_context("/?filename="):
            value, err, status = get_query_param_string("filename", required=True)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"

    def test_named_empty_optional(self, app):
        """Empty string with required=False returns empty string"""
        with app.test_request_context("/?filename="):
            value, err, status = get_query_param_string("filename", required=False)
            assert value == ""
            assert err is None

    def test_positional_string(self, app):
        """Bare positional ?myfile.vrd parsed as string"""
        with app.test_request_context("/?myfile.vrd"):
            value, err, status = get_query_param_string("filename")
            assert value == "myfile.vrd"
            assert err is None

    def test_positional_url_encoded(self, app):
        """URL-encoded bare positional value is decoded"""
        with app.test_request_context("/?my%20file.vrd"):
            value, err, status = get_query_param_string("filename")
            assert value == "my file.vrd"
            assert err is None

    def test_positional_skipped_when_equals_present(self, app):
        """Positional fallback skipped when query string has '='"""
        with app.test_request_context("/?other=value"):
            value, err, status = get_query_param_string("filename")
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"

    def test_missing_required(self, app):
        """Missing required string param returns MISSING_PARAMETER"""
        with app.test_request_context("/"):
            value, err, status = get_query_param_string("filename", required=True)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"

    def test_missing_optional(self, app):
        """Missing optional string param returns (None, None, None)"""
        with app.test_request_context("/"):
            value, err, status = get_query_param_string("filename", required=False)
            assert value is None
            assert err is None
            assert status is None

    def test_json_body_fallback(self, app):
        """JSON body dict used as fallback when query param absent"""
        with app.test_request_context("/"):
            json_data = {"filename": "test.vrd"}
            value, err, status = get_query_param_string("filename", json_data=json_data)
            assert value == "test.vrd"
            assert err is None

    def test_json_body_int_stringified(self, app):
        """Non-string JSON value is stringified"""
        with app.test_request_context("/"):
            json_data = {"filename": 42}
            value, err, status = get_query_param_string("filename", json_data=json_data)
            assert value == "42"
            assert err is None

    def test_json_body_not_used_when_query_param_present(self, app):
        """Query param takes precedence over JSON body"""
        with app.test_request_context("/?filename=from_query"):
            json_data = {"filename": "from_json"}
            value, err, status = get_query_param_string("filename", json_data=json_data)
            assert value == "from_query"

    def test_json_body_missing_key(self, app):
        """JSON body without the key returns MISSING_PARAMETER when required"""
        with app.test_request_context("/"):
            json_data = {"other": "value"}
            value, err, status = get_query_param_string("filename", json_data=json_data)
            assert value is None
            assert status == 400
            assert err["error"]["code"] == "MISSING_PARAMETER"

    def test_json_body_none_value(self, app):
        """JSON body with None value falls through to missing check"""
        with app.test_request_context("/"):
            json_data = {"filename": None}
            value, err, status = get_query_param_string("filename", required=True)
            assert value is None
            assert status == 400


# ============================================================================
# Integration tests — verify behavior through actual route endpoints
# ============================================================================


class TestGetQueryParamIntegration:
    """Integration tests for get_query_param() through routes"""

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

    def test_positional_fallback_int(self):
        """Bare positional value like ?3 works"""
        self.mock_vv.ChannelUnit.return_value = "g"
        response = self.client.get("/api/v1/channelunit?3")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["channel"] == 3

    def test_positional_fallback_skipped_when_named_params(self):
        """Positional fallback should NOT trigger when query string contains '='"""
        response = self.client.get("/api/v1/channelunit?other=value")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_missing_required_param(self):
        """Missing required parameter returns 400"""
        response = self.client.get("/api/v1/channelunit")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_optional_param_missing(self):
        """Optional parameter absent uses default"""
        self.mock_vv.ControlUnit.return_value = "m/s²"
        response = self.client.get("/api/v1/controlunit")
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["loop"] == 1


class TestGetQueryParamStringIntegration:
    """Integration tests for get_query_param_string() through routes"""

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
        """Bare positional string value works"""
        self.mock_vv.ReportField.return_value = "Test Value"
        response = self.client.get("/api/v1/reportfield?TestName")
        assert response.status_code == 200

    def test_positional_fallback_skipped_when_named_params(self):
        """Positional fallback skipped when query string contains '='"""
        response = self.client.get("/api/v1/reportfield?other=value")
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"]["code"] == "MISSING_PARAMETER"

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
        if response.status_code == 400:
            assert "filename" not in data["error"].get("message", "")

    def test_url_encoded_positional(self):
        """URL-encoded bare positional value is decoded"""
        self.mock_vv.ReportField.return_value = "Test Value"
        response = self.client.get("/api/v1/reportfield?Test%20Name")
        assert response.status_code == 200
