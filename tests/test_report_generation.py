# ============================================================================
# FILE: tests/test_report_generation.py (Report Generation Tests) - v1
# ============================================================================

"""
Test cases for report generation endpoints
Tests uploading VRD files and generating reports with templates
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from app import create_app, set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestReportGeneration:
    """Test report generation endpoints"""

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
    def sample_vrd_path(self):
        """Path to the sample VRD file relative to project root"""
        # Get the project root directory (one folder up from this test file)
        project_root = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(project_root)  # Go up one more level from tests/
        return os.path.join(project_root, "data", "2025Sep22-1633-0002.vrd")

    def test_generatereport_upload_with_template(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport with VRD file upload and Test Report.vvtemplate"""

        # Check if the sample VRD file exists
        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        # Read the VRD file content
        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        file_size = len(vrd_content)
        template_name = "Test Report.vvtemplate"
        output_name = "test_report_output.pdf"

        # Mock the GenerateReportFromVV function to return a success response
        mock_generated_path = "C:\\VibrationVIEW\\Reports\\test_report_output.pdf"

        with patch('routes.report_generation.GenerateReportFromVV') as mock_generate, \
             patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.send_file') as mock_send_file:

            mock_generate.return_value = mock_generated_path
            mock_exists.return_value = True
            mock_send_file.return_value = MagicMock()

            # Make the request
            response = client.post(
                f'/api/v1/generatereport?template_name={template_name}&output_name={output_name}',
                data=vrd_content,
                headers={
                    'Content-Length': str(file_size),
                    'Content-Type': 'application/octet-stream'
                }
            )

            # Verify send_file was called with correct parameters
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            assert call_args[0][0] == mock_generated_path
            assert call_args.kwargs['as_attachment'] is True
            assert call_args.kwargs['download_name'] == output_name

            # Verify GenerateReportFromVV was called correctly
            mock_generate.assert_called_once()
            gen_call_args = mock_generate.call_args[0]

            # Check that a temporary file path was used
            temp_file_path = gen_call_args[0]
            assert temp_file_path.endswith('.vrd')
            assert gen_call_args[1] == template_name  # template_name
            assert gen_call_args[2] == output_name    # output_name

    def test_generatereport_missing_template_name(self, client, mock_vv, sample_vrd_path):
        """Test PUT /generatereport with missing template_name parameter"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        response = client.post(
            '/api/v1/generatereport?output_name=test_report.pdf',  # Missing template_name
            data=vrd_content,
            headers={
                'Content-Length': str(len(vrd_content)),
                'Content-Type': 'application/octet-stream'
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Upload mode requires template_name query parameter' in data['error']['message']
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_generatereport_missing_output_name(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport with missing output_name parameter"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        response = client.post(
            '/api/v1/generatereport?template_name=Test Report.vvtemplate',  # Missing output_name
            data=vrd_content,
            headers={
                'Content-Length': str(len(vrd_content)),
                'Content-Type': 'application/octet-stream'
            }
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Upload mode requires output_name query parameter' in data['error']['message']
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_generatereport_empty_file_content(self, client, mock_vv):
        """Test POST /generatereport with empty file content"""

        # Setup mock to return None for last data file
        mock_vv.ReportField.return_value = None

        response = client.post(
            '/api/v1/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
            data=b'',  # Empty content
            headers={
                'Content-Length': '0',
                'Content-Type': 'application/octet-stream'
            }
        )

        # Empty content with Content-Length 0 should be handled as file path mode
        # Since no file_path provided and no last data file, should return 400
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'NO_DATA_FILE_AVAILABLE'

    def test_generatereport_file_too_large(self, client, mock_vv):
        """Test POST /generatereport with file exceeding size limit"""

        # Create a large content that exceeds the 100MB limit
        large_content = b'x' * (101 * 1024 * 1024)  # 101MB

        response = client.post(
            '/api/v1/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
            data=large_content,
            headers={
                'Content-Length': str(len(large_content)),
                'Content-Type': 'application/octet-stream'
            }
        )

        assert response.status_code == 413  # Payload Too Large
        data = response.get_json()
        assert data['success'] is False
        assert 'File too large (max 100MB)' in data['error']['message']
        assert data['error']['code'] == 'FILE_TOO_LARGE'

    def test_generatereport_generation_failure(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport when GenerateReportFromVV fails"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        with patch('routes.report_generation.GenerateReportFromVV') as mock_generate:
            mock_generate.side_effect = Exception("Report generation failed")

            response = client.post(
                '/api/v1/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
                data=vrd_content,
                headers={
                    'Content-Length': str(len(vrd_content)),
                    'Content-Type': 'application/octet-stream'
                }
            )

            assert response.status_code == 500
            data = response.get_json()
            assert data['success'] is False
            assert 'Failed to upload and generate report' in data['error']['message']
            assert data['error']['code'] == 'UPLOAD_REPORT_GENERATION_ERROR'

    def test_generatereport_path_validation_security(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport with path validation for output_name"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        # Test with malicious output path
        malicious_output = "..\\..\\Windows\\System32\\evil.exe"

        response = client.post(
            f'/api/v1/generatereport?template_name=Test Report.vvtemplate&output_name={malicious_output}',
            data=vrd_content,
            headers={
                'Content-Length': str(len(vrd_content)),
                'Content-Type': 'application/octet-stream'
            }
        )

        assert response.status_code == 403  # Forbidden due to path validation
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'OUTPUT_PATH_VALIDATION_ERROR'

    def test_generatereport_with_different_templates(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport with different template names"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        templates_to_test = [
            "Test Report.vvtemplate",
            "Custom Template.vvtemplate",
            "Standard Report.vvtemplate"
        ]

        for template_name in templates_to_test:
            with patch('routes.report_generation.GenerateReportFromVV') as mock_generate, \
                 patch('routes.report_generation.os.path.exists') as mock_exists, \
                 patch('routes.report_generation.send_file') as mock_send_file:

                mock_generated_path = f"C:\\VibrationVIEW\\Reports\\output_{template_name.replace(' ', '_')}.pdf"
                mock_generate.return_value = mock_generated_path
                mock_exists.return_value = True
                mock_send_file.return_value = MagicMock()

                response = client.post(
                    f'/api/v1/generatereport?template_name={template_name}&output_name=output.pdf',
                    data=vrd_content,
                    headers={
                        'Content-Length': str(len(vrd_content)),
                        'Content-Type': 'application/octet-stream'
                    }
                )

                # Verify send_file was called
                mock_send_file.assert_called_once()

                # Verify the correct template was used in the call
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args[0]
                assert call_args[1] == template_name  # template_name parameter



    def test_generatereport_with_special_characters_in_names(self, client, mock_vv, sample_vrd_path):
        """Test POST /generatereport with special characters in template and output names"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        template_name = "Test Report (v2.1).vvtemplate"
        output_name = "test_report_2025-09-22_final.pdf"

        with patch('routes.report_generation.GenerateReportFromVV') as mock_generate, \
             patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.send_file') as mock_send_file:

            mock_generated_path = "C:\\VibrationVIEW\\Reports\\test_report_2025-09-22_final.pdf"
            mock_generate.return_value = mock_generated_path
            mock_exists.return_value = True
            mock_send_file.return_value = MagicMock()

            response = client.post(
                f'/api/v1/generatereport?template_name={template_name}&output_name={output_name}',
                data=vrd_content,
                headers={
                    'Content-Length': str(len(vrd_content)),
                    'Content-Type': 'application/octet-stream'
                }
            )

            # Verify send_file was called with correct parameters
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            assert call_args[0][0] == mock_generated_path
            assert call_args.kwargs['as_attachment'] is True
            assert call_args.kwargs['download_name'] == output_name

            # Verify GenerateReportFromVV was called with correct template
            mock_generate.assert_called_once()
            gen_call_args = mock_generate.call_args[0]
            assert gen_call_args[1] == template_name
            assert gen_call_args[2] == output_name


class TestDatafileRoute:
    """Test datafile endpoint path validation security"""

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

    def test_datafile_rejects_path_traversal_dotdot(self, client, mock_vv):
        """Test that datafile rejects path traversal with .."""
        response = client.get('/api/v1/datafile?file_path=..\\..\\Windows\\System32\\config\\sam')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'Path traversal detected' in data['error']['message']

    def test_datafile_rejects_absolute_path_outside_authorized(self, client, mock_vv):
        """Test that datafile rejects absolute paths outside authorized directories"""
        response = client.get('/api/v1/datafile?file_path=C:\\Windows\\System32\\cmd.exe')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'not within authorized directories' in data['error']['message']

    def test_datafile_rejects_unix_path_traversal(self, client, mock_vv):
        """Test that datafile rejects Unix-style path traversal"""
        response = client.get('/api/v1/datafile?file_path=/../../../etc/passwd')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_datafile_rejects_encoded_path_traversal(self, client, mock_vv):
        """Test that datafile rejects encoded path traversal attempts"""
        # URL encoded ..
        response = client.get('/api/v1/datafile?file_path=%2e%2e%5c%2e%2e%5cWindows%5cSystem32%5ccmd.exe')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_datafile_rejects_multiple_colons(self, client, mock_vv):
        """Test that datafile rejects paths with multiple colons (potential ADS or injection)"""
        response = client.get('/api/v1/datafile?file_path=C:\\data\\file.vrd:hidden:$DATA')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'Path traversal detected' in data['error']['message']

    def test_datafile_allows_authorized_path(self, client, mock_vv):
        """Test that datafile allows paths within authorized directories"""
        from config import Config

        # Get an authorized directory
        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        test_file_path = os.path.join(authorized_dir, 'test_file.vrd')

        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False  # File doesn't exist but path should be validated

            response = client.get(f'/api/v1/datafile?file_path={test_file_path}')

            # Should pass path validation but fail on file not found
            assert response.status_code == 404
            data = response.get_json()
            assert data['error']['code'] == 'FILE_NOT_FOUND'

    def test_datafile_uses_last_datafile_when_no_path(self, client, mock_vv):
        """Test that datafile uses LastDataFile from VibrationVIEW when no path provided"""
        from config import Config

        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        last_data_file = os.path.join(authorized_dir, 'last_test.vrd')
        mock_vv.ReportField.return_value = last_data_file

        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False

            response = client.get('/api/v1/datafile')

            # Should try to use LastDataFile and fail on file not found
            assert response.status_code == 404
            mock_vv.ReportField.assert_called_with('LastDataFile')

    def test_datafile_post_rejects_path_traversal(self, client, mock_vv):
        """Test that datafile POST also rejects path traversal"""
        response = client.post(
            '/api/v1/datafile',
            json={'file_path': '..\\..\\Windows\\System32\\config\\sam'}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_datafile_returns_file_when_valid(self, client, mock_vv):
        """Test that datafile returns file content when path is valid and file exists"""
        from config import Config

        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        test_file_path = os.path.join(authorized_dir, 'test_file.vrd')

        with patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.send_file') as mock_send_file:

            mock_exists.return_value = True
            mock_send_file.return_value = MagicMock()

            response = client.get(f'/api/v1/datafile?file_path={test_file_path}')

            # send_file should have been called with the validated path
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            assert 'as_attachment' in call_args.kwargs
            assert call_args.kwargs['as_attachment'] is True


class TestDatafilesRoute:
    """Test datafiles endpoint that returns zip of all files in OutDir"""

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

    def test_datafiles_returns_zip_when_files_exist(self, client, mock_vv):
        """Test that datafiles returns a zip file when OutDir has files"""
        mock_out_dir = 'C:\\VibrationVIEW\\Data'
        mock_vv.ReportField.return_value = mock_out_dir

        with patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.os.path.isdir') as mock_isdir, \
             patch('routes.report_generation.os.listdir') as mock_listdir, \
             patch('routes.report_generation.os.path.isfile') as mock_isfile, \
             patch('routes.report_generation.zipfile.ZipFile') as mock_zipfile, \
             patch('routes.report_generation.send_file') as mock_send_file:

            mock_exists.return_value = True
            mock_isdir.return_value = True
            mock_listdir.return_value = ['file1.vrd', 'file2.vrd', 'file3.txt']
            mock_isfile.return_value = True
            mock_send_file.return_value = MagicMock()

            # Mock the ZipFile context manager
            mock_zip_instance = MagicMock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance

            response = client.get('/api/v1/datafiles')

            # Verify ReportField was called with OutDir
            mock_vv.ReportField.assert_called_with('OutDir')

            # Verify send_file was called
            mock_send_file.assert_called_once()
            call_args = mock_send_file.call_args
            assert call_args.kwargs['mimetype'] == 'application/zip'
            assert call_args.kwargs['as_attachment'] is True
            assert call_args.kwargs['download_name'].startswith('datafiles_')
            assert call_args.kwargs['download_name'].endswith('.zip')

    def test_datafiles_returns_error_when_no_outdir(self, client, mock_vv):
        """Test that datafiles returns error when OutDir is not configured"""
        mock_vv.ReportField.return_value = None

        response = client.get('/api/v1/datafiles')

        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'NO_OUTPUT_DIRECTORY'

    def test_datafiles_returns_error_when_directory_not_found(self, client, mock_vv):
        """Test that datafiles returns error when OutDir doesn't exist"""
        mock_out_dir = 'C:\\NonExistent\\Directory'
        mock_vv.ReportField.return_value = mock_out_dir

        with patch('routes.report_generation.os.path.exists') as mock_exists:
            mock_exists.return_value = False

            response = client.get('/api/v1/datafiles')

            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'DIRECTORY_NOT_FOUND'

    def test_datafiles_returns_error_when_path_not_directory(self, client, mock_vv):
        """Test that datafiles returns error when OutDir is not a directory"""
        mock_out_dir = 'C:\\VibrationVIEW\\somefile.txt'
        mock_vv.ReportField.return_value = mock_out_dir

        with patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.os.path.isdir') as mock_isdir:

            mock_exists.return_value = True
            mock_isdir.return_value = False

            response = client.get('/api/v1/datafiles')

            assert response.status_code == 400
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'NOT_A_DIRECTORY'

    def test_datafiles_returns_error_when_no_files(self, client, mock_vv):
        """Test that datafiles returns error when OutDir has no files"""
        mock_out_dir = 'C:\\VibrationVIEW\\Data'
        mock_vv.ReportField.return_value = mock_out_dir

        with patch('routes.report_generation.os.path.exists') as mock_exists, \
             patch('routes.report_generation.os.path.isdir') as mock_isdir, \
             patch('routes.report_generation.os.listdir') as mock_listdir:

            mock_exists.return_value = True
            mock_isdir.return_value = True
            mock_listdir.return_value = []  # Empty directory

            response = client.get('/api/v1/datafiles')

            assert response.status_code == 404
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'NO_FILES_FOUND'

    def test_datafiles_returns_error_when_reportfield_fails(self, client, mock_vv):
        """Test that datafiles returns error when ReportField raises exception"""
        mock_vv.ReportField.side_effect = Exception("COM error")

        response = client.get('/api/v1/datafiles')

        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'OUTPUT_DIRECTORY_ERROR'


class TestGenerateReportPathValidation:
    """Test generatereport endpoint path validation security"""

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

    def test_generatereport_rejects_path_traversal_dotdot(self, client, mock_vv):
        """Test that generatereport rejects path traversal with .."""
        response = client.get('/api/v1/generatereport?file_path=..\\..\\Windows\\System32\\config\\sam')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'Path traversal detected' in data['error']['message']

    def test_generatereport_rejects_absolute_path_outside_authorized(self, client, mock_vv):
        """Test that generatereport rejects absolute paths outside authorized directories"""
        response = client.get('/api/v1/generatereport?file_path=C:\\Windows\\System32\\cmd.exe')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'not within authorized directories' in data['error']['message']

    def test_generatereport_rejects_unix_path_traversal(self, client, mock_vv):
        """Test that generatereport rejects Unix-style path traversal"""
        response = client.get('/api/v1/generatereport?file_path=/../../../etc/passwd')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatereport_rejects_multiple_colons(self, client, mock_vv):
        """Test that generatereport rejects paths with multiple colons"""
        response = client.get('/api/v1/generatereport?file_path=C:\\data\\file.vrd:hidden:$DATA')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatereport_post_rejects_path_traversal(self, client, mock_vv):
        """Test that generatereport POST also rejects path traversal"""
        response = client.post(
            '/api/v1/generatereport',
            json={'file_path': '..\\..\\Windows\\System32\\config\\sam'}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatereport_rejects_malicious_output_path(self, client, mock_vv):
        """Test that generatereport rejects malicious output paths"""
        from config import Config
        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        valid_input = os.path.join(authorized_dir, 'test.vrd')

        with patch('routes.report_generation.os.path.exists') as mock_exists:
            mock_exists.return_value = True  # File exists, so we get to output validation

            response = client.get(
                f'/api/v1/generatereport?file_path={valid_input}&output_name=..\\..\\Windows\\evil.exe'
            )

            assert response.status_code == 403
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'OUTPUT_PATH_VALIDATION_ERROR'


class TestGenerateTxtPathValidation:
    """Test generatetxt endpoint path validation security"""

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

    def test_generatetxt_rejects_path_traversal_dotdot(self, client, mock_vv):
        """Test that generatetxt rejects path traversal with .."""
        response = client.get('/api/v1/generatetxt?file_path=..\\..\\Windows\\System32\\config\\sam')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'Path traversal detected' in data['error']['message']

    def test_generatetxt_rejects_absolute_path_outside_authorized(self, client, mock_vv):
        """Test that generatetxt rejects absolute paths outside authorized directories"""
        response = client.get('/api/v1/generatetxt?file_path=C:\\Windows\\System32\\cmd.exe')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'not within authorized directories' in data['error']['message']

    def test_generatetxt_rejects_unix_path_traversal(self, client, mock_vv):
        """Test that generatetxt rejects Unix-style path traversal"""
        response = client.get('/api/v1/generatetxt?file_path=/../../../etc/passwd')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatetxt_rejects_multiple_colons(self, client, mock_vv):
        """Test that generatetxt rejects paths with multiple colons"""
        response = client.get('/api/v1/generatetxt?file_path=C:\\data\\file.vrd:hidden:$DATA')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatetxt_post_rejects_path_traversal(self, client, mock_vv):
        """Test that generatetxt POST also rejects path traversal"""
        response = client.post(
            '/api/v1/generatetxt',
            json={'file_path': '..\\..\\Windows\\System32\\config\\sam'}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generatetxt_rejects_malicious_output_path(self, client, mock_vv):
        """Test that generatetxt rejects malicious output paths"""
        from config import Config
        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        valid_input = os.path.join(authorized_dir, 'test.vrd')

        with patch('routes.report_generation.os.path.exists') as mock_exists:
            mock_exists.return_value = True  # File exists, so we get to output validation

            response = client.get(
                f'/api/v1/generatetxt?file_path={valid_input}&output_name=..\\..\\Windows\\evil.txt'
            )

            assert response.status_code == 403
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'OUTPUT_PATH_VALIDATION_ERROR'


class TestGenerateUffPathValidation:
    """Test generateuff endpoint path validation security"""

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

    def test_generateuff_rejects_path_traversal_dotdot(self, client, mock_vv):
        """Test that generateuff rejects path traversal with .."""
        response = client.get('/api/v1/generateuff?file_path=..\\..\\Windows\\System32\\config\\sam')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'Path traversal detected' in data['error']['message']

    def test_generateuff_rejects_absolute_path_outside_authorized(self, client, mock_vv):
        """Test that generateuff rejects absolute paths outside authorized directories"""
        response = client.get('/api/v1/generateuff?file_path=C:\\Windows\\System32\\cmd.exe')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'
        assert 'not within authorized directories' in data['error']['message']

    def test_generateuff_rejects_unix_path_traversal(self, client, mock_vv):
        """Test that generateuff rejects Unix-style path traversal"""
        response = client.get('/api/v1/generateuff?file_path=/../../../etc/passwd')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generateuff_rejects_multiple_colons(self, client, mock_vv):
        """Test that generateuff rejects paths with multiple colons"""
        response = client.get('/api/v1/generateuff?file_path=C:\\data\\file.vrd:hidden:$DATA')

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generateuff_post_rejects_path_traversal(self, client, mock_vv):
        """Test that generateuff POST also rejects path traversal"""
        response = client.post(
            '/api/v1/generateuff',
            json={'file_path': '..\\..\\Windows\\System32\\config\\sam'}
        )

        assert response.status_code == 403
        data = response.get_json()
        assert data['success'] is False
        assert data['error']['code'] == 'PATH_VALIDATION_ERROR'

    def test_generateuff_rejects_malicious_output_path(self, client, mock_vv):
        """Test that generateuff rejects malicious output paths"""
        from config import Config
        authorized_dir = getattr(Config, 'DATA_FOLDER', None) or getattr(Config, 'REPORT_FOLDER', None)
        if not authorized_dir:
            pytest.skip("No authorized directory configured")

        valid_input = os.path.join(authorized_dir, 'test.vrd')

        with patch('routes.report_generation.os.path.exists') as mock_exists:
            mock_exists.return_value = True  # File exists, so we get to output validation

            response = client.get(
                f'/api/v1/generateuff?file_path={valid_input}&output_name=..\\..\\Windows\\evil.uff'
            )

            assert response.status_code == 403
            data = response.get_json()
            assert data['success'] is False
            assert data['error']['code'] == 'OUTPUT_PATH_VALIDATION_ERROR'