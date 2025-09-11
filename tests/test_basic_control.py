# ============================================================================
# FILE: tests/test_basic_control.py
# ============================================================================

"""
Tests for basic control routes, including template file upload functionality
"""

import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestBasicControl:
    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_opentest_template_file_upload(self, client):
        """Test uploading a template file (.vrandomt) via PUT /opentest"""
        
        # Read the actual template file (relative to tests folder)
        test_dir = os.path.dirname(__file__)
        template_file_path = os.path.join(test_dir, "..", "profiles", "random.vrandomt")
        
        with open(template_file_path, 'rb') as f:
            file_content = f.read()
        
        filename = "random.vrandomt"
        
        # Mock the registry path lookup
        mock_registry_path = r"C:\VibrationVIEW\New Test Defaults"
        
        with patch('routes.basic_control.get_new_test_defaults_path', return_value=mock_registry_path), \
             patch('routes.basic_control.handle_binary_upload') as mock_upload, \
             patch('os.makedirs') as mock_makedirs:
            
            # Configure the mock upload to simulate success
            mock_upload.return_value = (
                {
                    'FilePath': os.path.join(mock_registry_path, filename),
                    'Filename': filename,
                    'Size': len(file_content)
                },
                None,
                200
            )
            
            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True
            
            # Make the request
            response = client.put(
                f'/api/opentest?filename={filename}',
                data=file_content,
                headers={'Content-Length': str(len(file_content))}
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['result'] is True
            assert data['data']['filepath'] == filename
            assert data['data']['executed'] is True
            
            # Verify that handle_binary_upload was called with the correct parameters
            mock_upload.assert_called_once_with(
                filename,
                file_content,
                uploadsubfolder=mock_registry_path,
                usetemporaryfile=False
            )
            
            # Verify OpenTest was called
            self.mock_instance.OpenTest.assert_called_once()

    def test_opentest_template_file_upload_no_registry_fallback(self, client):
        """Test template file upload when registry path is not available (fallback)"""
        
        # Read the actual template file (relative to tests folder)
        test_dir = os.path.dirname(__file__)
        template_file_path = os.path.join(test_dir, "..", "profiles", "random.vrandomt")
        
        with open(template_file_path, 'rb') as f:
            file_content = f.read()
        
        filename = "test_template_fallback.vrandomt"
        
        # Mock registry path lookup to return None (simulating registry read failure)
        with patch('routes.basic_control.get_new_test_defaults_path', return_value=None), \
             patch('routes.basic_control.handle_binary_upload') as mock_upload:
            
            # Configure the mock upload to simulate success with regular upload folder
            mock_upload.return_value = (
                {
                    'FilePath': f"/regular/upload/path/{filename}",
                    'Filename': filename,
                    'Size': len(file_content)
                },
                None,
                200
            )
            
            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True
            
            # Make the request
            response = client.put(
                f'/api/opentest?filename={filename}',
                data=file_content,
                headers={'Content-Length': str(len(file_content))}
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify that handle_binary_upload was called with regular parameters (fallback)
            mock_upload.assert_called_once_with(filename, file_content)

    def test_opentest_regular_file_upload(self, client):
        """Test uploading a regular (non-template) file via PUT /opentest"""
        
        # Create dummy file content for a regular .vsp file
        file_content = b"dummy vsp file content"
        filename = "test_regular.vsp"
        
        with patch('routes.basic_control.handle_binary_upload') as mock_upload:
            
            # Configure the mock upload to simulate success
            mock_upload.return_value = (
                {
                    'FilePath': f"/regular/upload/path/{filename}",
                    'Filename': filename,
                    'Size': len(file_content)
                },
                None,
                200
            )
            
            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True
            
            # Make the request
            response = client.put(
                f'/api/opentest?filename={filename}',
                data=file_content,
                headers={'Content-Length': str(len(file_content))}
            )
            
            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify that handle_binary_upload was called with regular parameters
            # (no special template handling)
            mock_upload.assert_called_once_with(filename, file_content)

    def test_template_extension_detection(self):
        """Test the template extension detection utility function"""
        from utils.utils import is_template_file
        
        # Test template extensions
        template_files = [
            'test.vrandomt',
            'sine_test.vsinet',
            'shock_test.vshockt',
            'sor_test.vsort',
            'TEST.VRANDOMT'  # Test case insensitive
        ]
        
        for filename in template_files:
            assert is_template_file(filename) is True, f"Failed for {filename}"
        
        # Test non-template extensions
        regular_files = [
            'test.vsp',
            'test.vrp',
            'test.txt',
            'test.doc',
            'noextension'
        ]
        
        for filename in regular_files:
            assert is_template_file(filename) is False, f"Failed for {filename}"

    @patch('utils.utils.winreg')
    def test_registry_path_lookup_success(self, mock_winreg):
        """Test successful registry path lookup"""
        from utils.utils import get_new_test_defaults_path
        
        # Mock the registry operations
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = (r"C:\Test\NewDefaults", None)
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        
        result = get_new_test_defaults_path()
        
        assert result == r"C:\Test\NewDefaults"
        mock_winreg.OpenKey.assert_called_once()
        mock_winreg.QueryValueEx.assert_called_once_with(mock_key, "New Test Defaults")

    @patch('utils.utils.winreg')
    def test_registry_path_lookup_failure(self, mock_winreg):
        """Test registry path lookup when registry read fails"""
        from utils.utils import get_new_test_defaults_path
        
        # Mock registry failure
        mock_winreg.OpenKey.side_effect = FileNotFoundError("Registry key not found")
        mock_winreg.HKEY_CURRENT_USER = "HKCU"
        
        result = get_new_test_defaults_path()
        
        assert result is None

    def test_opentest_missing_filename_parameter(self, client):
        """Test PUT /opentest without filename parameter"""
        
        file_content = b"dummy content"
        
        response = client.put(
            '/api/opentest',  # No filename parameter
            data=file_content,
            headers={'Content-Length': str(len(file_content))}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Missing required query parameter: filename' in data['Error']

    def test_opentest_upload_error_handling(self, client):
        """Test PUT /opentest error handling from handle_binary_upload"""
        
        file_content = b"dummy content"
        filename = "test.vrandomt"
        
        # Mock handle_binary_upload to return an error
        with patch('routes.basic_control.handle_binary_upload') as mock_upload:
            mock_upload.return_value = (
                None,  # No result
                {'Error': 'File upload failed'},  # Error
                500  # Status code
            )
            
            response = client.put(
                f'/api/opentest?filename={filename}',
                data=file_content,
                headers={'Content-Length': str(len(file_content))}
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'File upload failed' in data['Error']