# ============================================================================
# FILE: tests/test_upload_size_limit.py
# ============================================================================

"""
Tests for MAX_CONTENT_LENGTH enforcement

Flask rejects requests larger than MAX_CONTENT_LENGTH before they reach
application code. These tests verify that oversized requests return a
JSON 413 response regardless of which endpoint is targeted.
"""

import pytest

from app import get_vv_instance


class TestUploadSizeLimit:

    @pytest.fixture(autouse=True)
    def _setup_mock(self, client):
        self.mock_instance = get_vv_instance()

    def test_oversized_post_returns_413(self, client):
        """Oversized POST body is rejected with 413 before reaching route handler"""
        large_body = b'x' * (11 * 1024 * 1024)  # 11 MB, default limit is 10 MB

        response = client.post(
            '/api/v1/opentest',
            data=large_body,
            content_type='application/octet-stream',
        )

        assert response.status_code == 413
        data = response.get_json()
        assert data['success'] is False
        assert 'exceeds' in data['message']

    def test_oversized_put_returns_413(self, client):
        """Oversized PUT body is rejected with 413"""
        large_body = b'x' * (11 * 1024 * 1024)

        response = client.put(
            '/api/v1/opentest',
            data=large_body,
            content_type='application/octet-stream',
        )

        assert response.status_code == 413
        data = response.get_json()
        assert data['success'] is False

    def test_within_limit_not_rejected(self, client):
        """Request within the size limit is not rejected as 413"""
        small_body = b'x' * 1024  # 1 KB

        response = client.post(
            '/api/v1/opentest?filename=test.vrp',
            data=small_body,
            content_type='application/octet-stream',
        )

        # Should not be 413 — may be another status depending on route logic
        assert response.status_code != 413

    def test_413_response_includes_limit(self, client):
        """413 response message includes the configured size limit"""
        large_body = b'x' * (11 * 1024 * 1024)

        response = client.post(
            '/api/v1/opentest',
            data=large_body,
            content_type='application/octet-stream',
        )

        assert response.status_code == 413
        data = response.get_json()
        assert '10MB' in data['message']

    def test_custom_limit_is_respected(self, app, client):
        """A lower MAX_CONTENT_LENGTH is enforced"""
        original_limit = app.config.get('MAX_CONTENT_LENGTH')
        app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 1 MB

        try:
            body = b'x' * (2 * 1024 * 1024)  # 2 MB

            response = client.post(
                '/api/v1/opentest',
                data=body,
                content_type='application/octet-stream',
            )

            assert response.status_code == 413
        finally:
            app.config['MAX_CONTENT_LENGTH'] = original_limit
