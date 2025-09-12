# ============================================================================
# FILE: tests/test_basic_control.py
# ============================================================================

"""
Tests for basic control routes, including template file upload functionality
"""

import os
import json
from unittest.mock import patch
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

        with open(template_file_path, "rb") as f:
            file_content = f.read()

        filename = "random.vrandomt"

        # Mock the registry path lookup
        mock_registry_path = r"C:\VibrationVIEW\New Test Defaults"

        with patch(
            "routes.basic_control.get_new_test_defaults_path",
            return_value=mock_registry_path,
        ), patch("routes.basic_control.handle_binary_upload") as mock_upload:

            # Configure the mock upload to simulate success
            mock_upload.return_value = (
                {
                    "FilePath": os.path.join(mock_registry_path, filename),
                    "Filename": filename,
                    "Size": len(file_content),
                },
                None,
                200,
            )

            # Configure mock VV instance (not actually called for default templates)
            self.mock_instance.OpenTest.return_value = True

            # Make the request
            response = client.put(
                f"/api/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["result"] is True
            assert data["data"]["copied_only"] is True
            assert data["data"]["executed"] is False

            # Verify that handle_binary_upload was called with the correct parameters
            mock_upload.assert_called_once_with(
                filename,
                file_content,
                uploadsubfolder=mock_registry_path,
                usetemporaryfile=False,
            )

            # Verify OpenTest was NOT called for default template files
            self.mock_instance.OpenTest.assert_not_called()

    def test_opentest_custom_template_file_upload(self, client):
        """Test uploading a custom (non-default) template file via PUT /opentest"""

        # Create dummy file content for a custom template
        file_content = b"custom template content"
        filename = "custom_test.vrandomt"  # Custom name, not in default template list

        # Mock the registry path lookup
        mock_registry_path = r"C:\VibrationVIEW\New Test Defaults"

        with patch(
            "routes.basic_control.get_new_test_defaults_path",
            return_value=mock_registry_path,
        ), patch("routes.basic_control.handle_binary_upload") as mock_upload:

            # Configure the mock upload to simulate success
            mock_upload.return_value = (
                {
                    "FilePath": os.path.join(mock_registry_path, filename),
                    "Filename": filename,
                    "Size": len(file_content),
                },
                None,
                200,
            )

            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True

            # Make the request
            response = client.put(
                f"/api/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["result"] is True
            assert data["data"]["executed"] is True
            assert "copied_only" not in data["data"]  # Should not have copied_only flag

            # Verify that handle_binary_upload was called with the correct parameters
            mock_upload.assert_called_once_with(
                filename,
                file_content,
                uploadsubfolder=mock_registry_path,
                usetemporaryfile=False,
            )

            # Verify OpenTest WAS called for custom template files
            self.mock_instance.OpenTest.assert_called_once()

    def test_opentest_template_file_upload_no_registry_fallback(self, client):
        """Test template file upload when registry path is not available (fallback)"""

        # Read the actual template file (relative to tests folder)
        test_dir = os.path.dirname(__file__)
        template_file_path = os.path.join(test_dir, "..", "profiles", "random.vrandomt")

        with open(template_file_path, "rb") as f:
            file_content = f.read()

        filename = "test_template_fallback.vrandomt"

        # Mock registry path lookup to return None (simulating registry read failure)
        with patch(
            "routes.basic_control.get_new_test_defaults_path", return_value=None
        ), patch("routes.basic_control.handle_binary_upload") as mock_upload:

            # Configure the mock upload to simulate success with regular upload folder
            mock_upload.return_value = (
                {
                    "FilePath": f"/regular/upload/path/{filename}",
                    "Filename": filename,
                    "Size": len(file_content),
                },
                None,
                200,
            )

            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True

            # Make the request
            response = client.put(
                f"/api/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

            # Verify that handle_binary_upload was called with regular parameters (fallback)
            mock_upload.assert_called_once_with(filename, file_content)

    def test_opentest_regular_file_upload(self, client):
        """Test uploading a regular (non-template) file via PUT /opentest"""

        # Create dummy file content for a regular .vsp file
        file_content = b"dummy vsp file content"
        filename = "test_regular.vsp"

        with patch("routes.basic_control.handle_binary_upload") as mock_upload:

            # Configure the mock upload to simulate success
            mock_upload.return_value = (
                {
                    "FilePath": f"/regular/upload/path/{filename}",
                    "Filename": filename,
                    "Size": len(file_content),
                },
                None,
                200,
            )

            # Configure mock VV instance
            self.mock_instance.OpenTest.return_value = True

            # Make the request
            response = client.put(
                f"/api/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

            # Verify that handle_binary_upload was called with regular parameters
            # (no special template handling)
            mock_upload.assert_called_once_with(filename, file_content)

    def test_template_extension_detection(self):
        """Test the template extension detection utility function"""
        from utils.utils import is_template_file

        # Test template extensions
        template_files = [
            "test.vrandomt",
            "sine_test.vsinet",
            "shock_test.vshockt",
            "sor_test.vsort",
            "TEST.VRANDOMT",  # Test case insensitive
        ]

        for filename in template_files:
            assert is_template_file(filename) is True, f"Failed for {filename}"

        # Test non-template extensions
        regular_files = ["test.vsp", "test.vrp", "test.txt", "test.doc", "noextension"]

        for filename in regular_files:
            assert is_template_file(filename) is False, f"Failed for {filename}"

    def test_opentest_missing_filename_parameter(self, client):
        """Test PUT /opentest without filename parameter"""

        file_content = b"dummy content"

        response = client.put(
            "/api/opentest",  # No filename parameter
            data=file_content,
            headers={"Content-Length": str(len(file_content))},
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Missing required query parameter: filename" in data["Error"]

    def test_opentest_upload_error_handling(self, client):
        """Test PUT /opentest error handling from handle_binary_upload"""

        file_content = b"dummy content"
        filename = "test.vrandomt"

        # Mock handle_binary_upload to return an error
        with patch("routes.basic_control.handle_binary_upload") as mock_upload:
            mock_upload.return_value = (
                None,  # No result
                {"Error": "File upload failed"},  # Error
                500,  # Status code
            )

            response = client.put(
                f"/api/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "File upload failed" in data["Error"]
