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
                f"/api/v1/opentest?filename={filename}",
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
                f"/api/v1/opentest?filename={filename}",
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
                f"/api/v1/opentest?filename={filename}",
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
                f"/api/v1/opentest?filename={filename}",
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
            "/api/v1/opentest",  # No filename parameter
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
                f"/api/v1/opentest?filename={filename}",
                data=file_content,
                headers={"Content-Length": str(len(file_content))},
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "File upload failed" in data["Error"]

    def test_closetest_get_success(self, client):
        """Test GET /closetest with successful profile close"""
        profile_name = "Random_Profile.vrpj"

        # Configure mock to return success
        self.mock_instance.CloseTest.return_value = True

        response = client.get(f"/api/v1/closetest?profilename={profile_name}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is True
        assert data["data"]["profile_name"] == profile_name
        assert "CloseTest command executed" in data["message"]

        # Verify the COM method was called with correct parameters
        self.mock_instance.CloseTest.assert_called_once_with(profile_name)

    def test_closetest_post_success(self, client):
        """Test POST /closetest with successful profile close"""
        profile_name = "Random_Profile.vrpj"

        # Configure mock to return success
        self.mock_instance.CloseTest.return_value = True

        response = client.post(f"/api/v1/closetest?profilename={profile_name}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is True
        assert data["data"]["profile_name"] == profile_name

        # Verify the COM method was called
        self.mock_instance.CloseTest.assert_called_once_with(profile_name)

    def test_closetest_unnamed_parameter(self, client):
        """Test /closetest with unnamed parameter syntax"""
        profile_name = "Random_Profile.vrpj"

        # Configure mock
        self.mock_instance.CloseTest.return_value = True

        # Use unnamed parameter (query string without '=')
        response = client.get(f"/api/v1/closetest?{profile_name}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["profile_name"] == profile_name

    def test_closetest_not_closed(self, client):
        """Test /closetest when profile was not closed (returns False)"""
        profile_name = "nonexistent_profile.vsp"

        # Configure mock to return False (profile not closed)
        self.mock_instance.CloseTest.return_value = False

        response = client.get(f"/api/v1/closetest?profilename={profile_name}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is False

    def test_closetest_missing_parameter(self, client):
        """Test /closetest without required profile name parameter"""
        response = client.get("/api/v1/closetest")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Missing required query parameter: profilename" in data["error"]["message"]

    def test_closetab_get_success(self, client):
        """Test GET /closetab with successful tab close"""
        tab_index = 0

        # Configure mock to return success
        self.mock_instance.CloseTab.return_value = True

        response = client.get(f"/api/v1/closetab?tabindex={tab_index}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is True
        assert data["data"]["tab_index"] == tab_index
        assert "CloseTab command executed" in data["message"]

        # Verify the COM method was called with correct parameters
        self.mock_instance.CloseTab.assert_called_once_with(tab_index)

    def test_closetab_post_success(self, client):
        """Test POST /closetab with successful tab close"""
        tab_index = 2

        # Configure mock to return success
        self.mock_instance.CloseTab.return_value = True

        response = client.post(f"/api/v1/closetab?tabindex={tab_index}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is True
        assert data["data"]["tab_index"] == tab_index

        # Verify the COM method was called
        self.mock_instance.CloseTab.assert_called_once_with(tab_index)

    def test_closetab_unnamed_parameter(self, client):
        """Test /closetab with unnamed parameter syntax"""
        tab_index = 1

        # Configure mock
        self.mock_instance.CloseTab.return_value = True

        # Use unnamed parameter (query string without '=')
        response = client.get(f"/api/v1/closetab?{tab_index}")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["test_was_closed"] is True
        assert data["data"]["tab_index"] == tab_index

    def test_closetab_not_closed(self, client):
        """Test /closetab when tab was not closed (returns False)"""
        tab_index = 99  # Invalid tab index

        # Configure mock to return False (tab not closed)
        self.mock_instance.CloseTab.return_value = False

        response = client.get(f"/api/v1/closetab?tabindex={tab_index}")

        assert response.status_code == 405
        data = json.loads(response.data)
        assert data["success"] is False
        assert data["error"]["code"] == "TAB_NOT_CLOSED"
        assert f"Tab {tab_index} could not be closed" in data["error"]["message"]

    def test_closetab_missing_parameter(self, client):
        """Test /closetab without required tab index parameter"""
        response = client.get("/api/v1/closetab")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Missing required query parameter: tabindex" in data["error"]["message"]
        assert data["error"]["code"] == "MISSING_PARAMETER"

    def test_closetab_invalid_parameter(self, client):
        """Test /closetab with invalid (non-integer) tab index"""
        response = client.get("/api/v1/closetab?tabindex=invalid")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Invalid tab index" in data["error"]["message"]
        assert "Must be an integer" in data["error"]["message"]

    def test_listopentests_success_with_tests(self, client):
        """Test GET /listopentests with multiple open tests"""
        open_tests = [
            ["1", "Random", "C:\\VibrationVIEW\\Profiles\\Random_Profile.vrpj", "Random_Profile"],
            ["2", "Sine", "C:\\VibrationVIEW\\Profiles\\test2.vrp", "test2"],
            ["3", "Shock", "C:\\VibrationVIEW\\Profiles\\test3.vsp", "test3"]
        ]

        # Configure mock to return list of open tests (2D array)
        self.mock_instance.ListOpenTests.return_value = tuple(open_tests)

        response = client.get("/api/v1/listopentests")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["open_tests"] == open_tests
        assert data["data"]["count"] == 3
        assert "columns" in data["data"]
        assert data["data"]["columns"] == ["Tab Index", "Test Type", "File Path", "Test Name"]
        assert "3 test(s) open" in data["message"]

        # Verify the COM method was called
        self.mock_instance.ListOpenTests.assert_called_once()

    def test_listopentests_success_no_tests(self, client):
        """Test GET /listopentests with no open tests"""
        # Configure mock to return empty tuple
        self.mock_instance.ListOpenTests.return_value = tuple()

        response = client.get("/api/v1/listopentests")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["open_tests"] == []
        assert data["data"]["count"] == 0
        assert "columns" in data["data"]
        assert data["data"]["columns"] == ["Tab Index", "Test Type", "File Path", "Test Name"]
        assert "0 test(s) open" in data["message"]

    def test_listopentests_none_return(self, client):
        """Test GET /listopentests when COM method returns None"""
        # Configure mock to return None (edge case)
        self.mock_instance.ListOpenTests.return_value = None

        response = client.get("/api/v1/listopentests")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["open_tests"] == []
        assert data["data"]["count"] == 0
        assert "columns" in data["data"]
        assert data["data"]["columns"] == ["Tab Index", "Test Type", "File Path", "Test Name"]
