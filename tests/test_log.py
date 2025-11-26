# ============================================================================
# FILE: tests/test_log.py
# ============================================================================

"""
Tests for Log Routes
"""

import pytest
import json
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestLogRoutes:
    """Tests for the log module endpoints"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_vv = MockVibrationVIEW()
        set_vv_instance(self.mock_vv)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_log_endpoint_returns_events(self, client):
        """Test GET /log returns parsed event log"""
        # Setup mock to return tab-separated event data
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tTest started\r\n10:00:05\tWarning\tLevel high"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data['data']
        assert 'count' in data['data']

        # Verify ReportField was called with 'Events'
        self.mock_vv.ReportField.assert_called_with('Events')

    def test_log_endpoint_parses_tsv_correctly(self, client):
        """Test that TSV event data is parsed into structured objects"""
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tTest started\r\n10:00:05\tWarning\tLevel high"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        events = data['data']['events']

        assert len(events) == 2
        assert events[0]['Time'] == '10:00:00'
        assert events[0]['Type'] == 'Info'
        assert events[0]['Message'] == 'Test started'
        assert events[1]['Time'] == '10:00:05'
        assert events[1]['Type'] == 'Warning'
        assert events[1]['Message'] == 'Level high'

    def test_log_endpoint_returns_count(self, client):
        """Test that the response includes correct event count"""
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tEvent 1\r\n10:00:01\tInfo\tEvent 2\r\n10:00:02\tInfo\tEvent 3"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['count'] == 3

    def test_log_endpoint_handles_empty_log(self, client):
        """Test handling of empty event log"""
        self.mock_vv.ReportField.return_value = ""

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'events' in data['data']

    def test_log_endpoint_handles_header_only(self, client):
        """Test handling when only headers are present (no events)"""
        mock_events = "Time\tType\tMessage"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # ParseVvTable returns raw text when less than 2 lines
        assert data['data']['count'] == 1
        assert 'RawText' in data['data']['events'][0]

    def test_log_docs_endpoint(self, client):
        """Test GET /docs/log returns documentation"""
        response = client.get('/api/v1/docs/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['module'] == 'log'
        assert 'endpoints' in data
        assert 'GET /log' in data['endpoints']


class TestLogEdgeCases:
    """Edge case tests for log module"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_vv = MockVibrationVIEW()
        set_vv_instance(self.mock_vv)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_log_with_special_characters(self, client):
        """Test handling of special characters in event messages"""
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tFile: C:\\path\\file.txt"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        events = data['data']['events']
        assert len(events) == 1
        assert 'C:\\path\\file.txt' in events[0]['Message']

    def test_log_with_unicode(self, client):
        """Test handling of unicode characters in events"""
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tTemperature: 25°C"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        events = data['data']['events']
        assert '25°C' in events[0]['Message']

    def test_log_with_malformed_line(self, client):
        """Test handling of malformed lines (wrong number of columns)"""
        # Line with only 2 columns instead of 3
        mock_events = "Time\tType\tMessage\r\n10:00:00\tInfo\tGood line\r\n10:00:01\tBadLine\r\n10:00:02\tInfo\tAnother good line"
        self.mock_vv.ReportField.return_value = mock_events

        response = client.get('/api/v1/log')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Malformed line should be skipped
        events = data['data']['events']
        assert len(events) == 2
