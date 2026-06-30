# ============================================================================
# FILE: tests/test_threading.py (Multi-threading singleton tests)
# ============================================================================

"""
Tests that verify the VibrationVIEW singleton behaves correctly when
accessed from multiple threads concurrently.
"""

import threading

import pytest

from app import create_app, reset_vv_instance, set_vv_instance
from config import TestingConfig
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


@pytest.fixture
def threaded_app():
    """Create app with mock for threading tests."""
    mock = MockVibrationVIEW()
    set_vv_instance(mock)
    app = create_app(TestingConfig)
    app.config["TESTING"] = True
    yield app, mock
    reset_vv_instance()


class TestThreadedAccess:
    """Test concurrent access to the singleton from multiple threads."""

    def test_concurrent_requests_return_same_instance(self, threaded_app):
        """All threads should get the same singleton instance."""
        app, mock = threaded_app
        client = app.test_client()
        results = {}
        errors = []

        def make_request(thread_id):
            try:
                response = client.get("/api/v1/isready")
                results[thread_id] = response.status_code
            except Exception as e:
                errors.append((thread_id, str(e)))

        threads = [threading.Thread(target=make_request, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        assert all(code == 200 for code in results.values()), f"Unexpected status codes: {results}"

    def test_concurrent_requests_all_succeed(self, threaded_app):
        """Multiple endpoints called concurrently should all succeed."""
        app, mock = threaded_app
        client = app.test_client()
        results = {}
        errors = []

        endpoints = [
            "/api/v1/isready",
            "/api/v1/isrunning",
            "/api/v1/isready",
            "/api/v1/isrunning",
            "/api/v1/isready",
        ]

        def make_request(idx, endpoint):
            try:
                response = client.get(endpoint)
                results[idx] = (endpoint, response.status_code)
            except Exception as e:
                errors.append((endpoint, str(e)))

        threads = [threading.Thread(target=make_request, args=(i, ep)) for i, ep in enumerate(endpoints)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"
        assert all(code == 200 for _, code in results.values()), f"Unexpected status codes: {results}"

    def test_rapid_sequential_requests_across_threads(self, threaded_app):
        """Rapid requests from different threads should not corrupt state."""
        app, mock = threaded_app
        client = app.test_client()
        errors = []
        response_count_lock = threading.Lock()
        response_count = [0]

        def burst(thread_id, count):
            for i in range(count):
                try:
                    response = client.get("/api/v1/isready")
                    if response.status_code != 200:
                        errors.append((thread_id, i, response.status_code))
                    with response_count_lock:
                        response_count[0] += 1
                except Exception as e:
                    errors.append((thread_id, i, str(e)))

        thread_count = 5
        requests_per_thread = 20
        threads = [threading.Thread(target=burst, args=(i, requests_per_thread)) for i in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"Thread errors: {errors}"
        assert response_count[0] == thread_count * requests_per_thread

    def test_singleton_not_none_under_contention(self, threaded_app):
        """get_vv_instance should never return None when a mock is set."""
        app, mock = threaded_app
        none_results = []

        def check_instance(thread_id):
            with app.app_context():
                from utils.vv_singleton import get_vv_instance

                instance = get_vv_instance()
                if instance is None:
                    none_results.append(thread_id)

        threads = [threading.Thread(target=check_instance, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not none_results, f"Threads got None: {none_results}"

