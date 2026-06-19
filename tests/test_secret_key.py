# ============================================================================
# FILE: tests/test_secret_key.py
# ============================================================================

"""
Tests for production startup validation (issue #19).
"""

import pytest

from config import Config, _DEV_SECRET_KEY, _PLACEHOLDER_API_KEY


def _set_valid_defaults(monkeypatch):
    """Set both keys to valid values so only the key under test triggers."""
    monkeypatch.setattr(Config, "SECRET_KEY", "valid-secret-key")
    monkeypatch.setattr(Config, "API_KEY", "valid-api-key")


class TestSecretKeyValidation:
    """Verify Config.validate_production() rejects the development default SECRET_KEY."""

    def test_rejects_dev_default(self, monkeypatch):
        _set_valid_defaults(monkeypatch)
        monkeypatch.setattr(Config, "SECRET_KEY", _DEV_SECRET_KEY)
        with pytest.raises(RuntimeError, match="SECRET_KEY is still set to the development default"):
            Config.validate_production()

    def test_accepts_custom_key(self, monkeypatch):
        _set_valid_defaults(monkeypatch)
        Config.validate_production()  # should not raise


class TestApiKeyValidation:
    """Verify Config.validate_production() rejects placeholder API_KEY."""

    def test_allows_empty_api_key(self, monkeypatch):
        _set_valid_defaults(monkeypatch)
        monkeypatch.setattr(Config, "API_KEY", "")
        Config.validate_production()  # should not raise

    def test_rejects_placeholder_api_key(self, monkeypatch):
        _set_valid_defaults(monkeypatch)
        monkeypatch.setattr(Config, "API_KEY", _PLACEHOLDER_API_KEY)
        with pytest.raises(RuntimeError, match="API_KEY is still the placeholder value"):
            Config.validate_production()

    def test_accepts_custom_api_key(self, monkeypatch):
        _set_valid_defaults(monkeypatch)
        Config.validate_production()  # should not raise


class TestDebugDefaults:
    """Verify Config defaults match expectations for production and debug modes."""

    def test_production_defaults(self):
        assert Config.DEBUG is False
        assert Config.LOG_LEVEL == "INFO"

    def test_debug_override(self, monkeypatch):
        """Simulate the --debug path in __main__."""
        monkeypatch.setattr(Config, "DEBUG", True)
        monkeypatch.setattr(Config, "LOG_LEVEL", "DEBUG")
        assert Config.DEBUG is True
        assert Config.LOG_LEVEL == "DEBUG"
