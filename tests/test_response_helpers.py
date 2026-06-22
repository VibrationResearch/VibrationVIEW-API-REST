# ============================================================================
# FILE: tests/test_response_helpers.py
# ============================================================================

"""
Tests for response helper utilities (issue #18).

Verifies that all response timestamps are UTC with explicit timezone.
"""

from datetime import datetime, timezone

from utils.response_helpers import error_response, success_response


class TestTimestampsAreUTC:
    """All response timestamps must be UTC with +00:00 suffix."""

    def test_success_response_has_utc_timestamp(self):
        resp = success_response({"ok": True})
        ts = datetime.fromisoformat(resp["timestamp"])
        assert ts.tzinfo is not None
        assert ts.utcoffset().total_seconds() == 0

    def test_error_response_has_utc_timestamp(self):
        resp = error_response("something failed")
        ts = datetime.fromisoformat(resp["timestamp"])
        assert ts.tzinfo is not None
        assert ts.utcoffset().total_seconds() == 0

    def test_timestamp_ends_with_utc_offset(self):
        resp = success_response()
        assert resp["timestamp"].endswith("+00:00")
