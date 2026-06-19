# ============================================================================
# FILE: tests/test_sanitize_nan.py
# ============================================================================

"""
Tests for NaN/Inf sanitization (issue #17).

Verifies that sanitize_nan handles all value types and that the custom
JSON provider applies it globally so individual routes don't need to call it.
"""

import pytest

from app import _sanitize_nan as sanitize_nan


class TestSanitizeNan:
    """sanitize_nan replaces NaN and Inf with None recursively."""

    def test_nan_replaced(self):
        assert sanitize_nan(float("nan")) is None

    def test_inf_replaced(self):
        assert sanitize_nan(float("inf")) is None

    def test_neg_inf_replaced(self):
        assert sanitize_nan(float("-inf")) is None

    def test_normal_float_unchanged(self):
        assert sanitize_nan(3.14) == 3.14

    def test_zero_unchanged(self):
        assert sanitize_nan(0.0) == 0.0

    def test_string_unchanged(self):
        assert sanitize_nan("hello") == "hello"

    def test_int_unchanged(self):
        assert sanitize_nan(42) == 42

    def test_none_unchanged(self):
        assert sanitize_nan(None) is None

    def test_list_with_nan(self):
        result = sanitize_nan([1.0, float("nan"), 3.0])
        assert result == [1.0, None, 3.0]

    def test_tuple_with_inf(self):
        result = sanitize_nan((float("inf"), 2.0))
        assert result == [None, 2.0]

    def test_dict_with_nan(self):
        result = sanitize_nan({"a": float("nan"), "b": 1.0})
        assert result == {"a": None, "b": 1.0}

    def test_nested_dict(self):
        result = sanitize_nan({"outer": {"inner": float("-inf")}})
        assert result == {"outer": {"inner": None}}

    def test_dict_with_list(self):
        result = sanitize_nan({"data": [float("nan"), 1.0, float("inf")]})
        assert result == {"data": [None, 1.0, None]}


class TestNaNSafeJSONProvider:
    """The Flask app JSON provider converts NaN/Inf to null in responses."""

    @pytest.fixture
    def client(self):
        from app import create_app, set_vv_instance
        from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW

        mock_vv = MockVibrationVIEW()
        set_vv_instance(mock_vv)
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client
        from app import reset_vv_instance

        reset_vv_instance()

    def test_nan_in_response_becomes_null(self, client):
        """Verify jsonify converts NaN to null via the custom provider."""
        from flask import jsonify

        from app import create_app

        app = create_app()
        with app.app_context():
            response = jsonify({"value": float("nan"), "normal": 1.0})
            data = response.get_json()
            assert data["value"] is None
            assert data["normal"] == 1.0

    def test_inf_in_response_becomes_null(self, client):
        """Verify jsonify converts Inf to null via the custom provider."""
        from flask import jsonify

        from app import create_app

        app = create_app()
        with app.app_context():
            response = jsonify({"value": float("inf")})
            data = response.get_json()
            assert data["value"] is None
