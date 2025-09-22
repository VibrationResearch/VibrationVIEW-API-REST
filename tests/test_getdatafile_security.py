# ============================================================================
# FILE: tests/test_getdatafile_security.py (GetDataFile Security Tests) - v1
# ============================================================================

"""
Test cases for /getdatafile path validation security
Ensures that the route only allows access to files within authorized directories
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch
from app import create_app, set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW
from config import Config


class TestGetDataFileSecurity:
    """Test security aspects of /getdatafile endpoint"""

    @pytest.fixture
    def app(self):
        """Create test app"""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def mock_vv(self):
        """Create and set mock VibrationVIEW instance"""
        reset_vv_instance()
        mock_instance = MockVibrationVIEW()
        set_vv_instance(mock_instance)
        yield mock_instance
        reset_vv_instance()

    @pytest.fixture
    def mock_config(self):
        """Mock configuration with test directories"""
        with patch.object(Config, 'REPORT_FOLDER', 'C:\\VibrationVIEW\\Reports'), \
             patch.object(Config, 'PROFILE_FOLDER', 'C:\\VibrationVIEW\\Profiles'), \
             patch.object(Config, 'DATA_FOLDER', 'C:\\VibrationVIEW\\Data'):
            yield

    def test_getdatafile_valid_path_in_data_folder(self, client, mock_vv, mock_config):
        """Test /getdatafile with valid path in DATA_FOLDER"""
        # Create a temporary file to simulate a valid data file
        with tempfile.NamedTemporaryFile(suffix='.vrd', delete=False) as temp_file:
            temp_file.write(b'mock vrd data')
            temp_file_path = temp_file.name

        try:
            # Mock the path to appear within DATA_FOLDER
            data_folder_path = "C:\\VibrationVIEW\\Data\\test.vrd"

            with patch('os.path.exists') as mock_exists, \
                 patch('os.path.getsize') as mock_getsize, \
                 patch('utils.path_validator.is_path_within_authorized_directories') as mock_auth, \
                 patch('flask.send_file') as mock_send:

                mock_exists.return_value = True
                mock_getsize.return_value = 1024
                mock_auth.return_value = True
                mock_send.return_value = "mock file response"

                response = client.get(f'/api/getdatafile?file_path={data_folder_path}')

                assert response.status_code == 200
                mock_send.assert_called_once()

        finally:
            # Clean up
            try:
                os.unlink(temp_file_path)
            except:
                pass

    def test_getdatafile_invalid_path_outside_authorized_dirs(self, client, mock_vv, mock_config):
        """Test /getdatafile rejects paths outside authorized directories"""
        malicious_path = "C:\\Windows\\System32\\evil.exe"

        response = client.get(f'/api/getdatafile?file_path={malicious_path}')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not within authorized directories' in data['error']['message']
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_getdatafile_path_traversal_attack(self, client, mock_vv, mock_config):
        """Test /getdatafile prevents path traversal attacks"""
        traversal_path = "C:\\VibrationVIEW\\Data\\..\\..\\Windows\\System32\\cmd.exe"

        response = client.get(f'/api/getdatafile?file_path={traversal_path}')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Path traversal detected' in data['error']['message']
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_getdatafile_relative_path_attack(self, client, mock_vv, mock_config):
        """Test /getdatafile rejects relative path attacks"""
        relative_path = "../../../etc/passwd"

        response = client.get(f'/api/getdatafile?file_path={relative_path}')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Path traversal detected' in data['error']['message']
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_getdatafile_empty_path(self, client, mock_vv, mock_config):
        """Test /getdatafile with empty path parameter"""
        # Setup mock to return no last data file
        mock_vv.ReportField.return_value = None

        response = client.get('/api/getdatafile?file_path=')

        # Should try to get last data file, which returns None
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No file_path provided and no last data file available' in data['error']['message']
        assert data['error']['code'] == 'NO_DATA_FILE_AVAILABLE'

    def test_getdatafile_no_path_uses_last_data_file(self, client, mock_vv, mock_config):
        """Test /getdatafile without path parameter uses last data file"""
        # Setup mock to return a valid last data file in authorized directory
        last_data_file = "C:\\VibrationVIEW\\Data\\last_test.vrd"
        mock_vv.ReportField.return_value = last_data_file

        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize, \
             patch('utils.path_validator.is_path_within_authorized_directories') as mock_auth, \
             patch('flask.send_file') as mock_send:

            mock_exists.return_value = True
            mock_getsize.return_value = 2048
            mock_auth.return_value = True
            mock_send.return_value = "mock file response"

            response = client.get('/api/getdatafile')

            assert response.status_code == 200
            mock_send.assert_called_once()
            # Verify that ReportField was called to get last data file
            mock_vv.ReportField.assert_called_with('LastDataFile')

    def test_getdatafile_last_data_file_outside_authorized_dirs(self, client, mock_vv, mock_config):
        """Test /getdatafile rejects last data file if outside authorized directories"""
        # Setup mock to return a last data file outside authorized directories
        last_data_file = "C:\\Temp\\unauthorized.vrd"
        mock_vv.ReportField.return_value = last_data_file

        response = client.get('/api/getdatafile')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not within authorized directories' in data['error']['message']
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_getdatafile_post_method_with_json(self, client, mock_vv, mock_config):
        """Test /getdatafile POST method with JSON body"""
        data_folder_path = "C:\\VibrationVIEW\\Data\\test_post.vrd"

        with patch('os.path.exists') as mock_exists, \
             patch('os.path.getsize') as mock_getsize, \
             patch('utils.path_validator.is_path_within_authorized_directories') as mock_auth, \
             patch('flask.send_file') as mock_send:

            mock_exists.return_value = True
            mock_getsize.return_value = 1024
            mock_auth.return_value = True
            mock_send.return_value = "mock file response"

            response = client.post('/api/getdatafile',
                                 json={'file_path': data_folder_path},
                                 content_type='application/json')

            assert response.status_code == 200
            mock_send.assert_called_once()

    def test_getdatafile_post_method_malicious_json(self, client, mock_vv, mock_config):
        """Test /getdatafile POST method rejects malicious paths in JSON"""
        malicious_path = "C:\\Windows\\System32\\evil.exe"

        response = client.post('/api/getdatafile',
                             json={'file_path': malicious_path},
                             content_type='application/json')

        assert response.status_code == 403
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'not within authorized directories' in data['error']['message']
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_getdatafile_file_not_found_after_validation(self, client, mock_vv, mock_config):
        """Test /getdatafile handles file not found after path validation"""
        # Valid path in authorized directory but file doesn't exist
        valid_but_missing_path = "C:\\VibrationVIEW\\Data\\nonexistent.vrd"

        with patch('utils.path_validator.is_path_within_authorized_directories') as mock_auth:
            mock_auth.return_value = True

            response = client.get(f'/api/getdatafile?file_path={valid_but_missing_path}')

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'File not found' in data['error']['message']
            assert data['error']['code'] == 'FILE_NOT_FOUND'