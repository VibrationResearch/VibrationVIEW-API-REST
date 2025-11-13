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
        """Test PUT /generatereport with VRD file upload and Test Report.vvtemplate"""

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

        with patch('routes.report_generation.GenerateReportFromVV') as mock_generate:
            mock_generate.return_value = mock_generated_path

            # Mock file operations and provide mock file content
            mock_file_content = b"Mock PDF content for testing"
            import base64
            mock_base64_content = base64.b64encode(mock_file_content).decode('utf-8')

            with patch('os.path.exists') as mock_exists, \
                 patch('os.path.getsize') as mock_getsize, \
                 patch('builtins.open', create=True) as mock_open:

                mock_exists.return_value = True
                mock_getsize.return_value = len(mock_file_content)

                # Mock file reading to return our test content
                mock_file = MagicMock()
                mock_file.read.return_value = mock_file_content
                mock_open.return_value.__enter__.return_value = mock_file

                # Make the request
                response = client.post(
                    f'/api/generatereport?template_name={template_name}&output_name={output_name}',
                    data=vrd_content,
                    headers={
                        'Content-Length': str(file_size),
                        'Content-Type': 'application/octet-stream'
                    }
                )

                # Verify the response
                assert response.status_code == 200

                data = response.get_json()
                assert data['success'] is True
                assert data['data']['generated_file_path'] == mock_generated_path
                assert data['data']['template_name'] == template_name
                assert data['data']['output_name'] == output_name
                assert data['data']['used_upload'] is True  # Verify upload mode was used
                assert data['data']['file_exists'] is True
                assert data['data']['file_size'] == len(mock_file_content)

                # Verify file content is included
                assert 'content' in data['data']
                assert data['data']['content'] == mock_base64_content
                assert data['data']['is_binary'] is True

                # Save the generated file content to logs folder
                try:
                    # Get project root (two levels up from test file)
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    logs_dir = os.path.join(project_root, "logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    # Save the mock file content
                    saved_filename = f"test_output_{template_name.replace(' ', '_').replace('.', '_')}.pdf"
                    saved_path = os.path.join(logs_dir, saved_filename)

                    with open(saved_path, 'wb') as f:
                        f.write(mock_file_content)

                    print(f"Saved test output to: {saved_path} ({len(mock_file_content)} bytes)")

                except Exception as e:
                    print(f"Failed to save test output to logs: {e}")

                # Verify GenerateReportFromVV was called correctly
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args[0]

                # Check that a temporary file path was used
                temp_file_path = call_args[0]
                assert temp_file_path.endswith('.vrd')
                assert call_args[1] == template_name  # template_name
                assert call_args[2] == output_name    # output_name

    def test_generatereport_missing_template_name(self, client, mock_vv, sample_vrd_path):
        """Test PUT /generatereport with missing template_name parameter"""

        if not os.path.exists(sample_vrd_path):
            pytest.skip(f"Sample VRD file not found: {sample_vrd_path}")

        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        response = client.post(
            '/api/generatereport?output_name=test_report.pdf',  # Missing template_name
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
            '/api/generatereport?template_name=Test Report.vvtemplate',  # Missing output_name
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
            '/api/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
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
            '/api/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
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
                '/api/generatereport?template_name=Test Report.vvtemplate&output_name=test.pdf',
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
            f'/api/generatereport?template_name=Test Report.vvtemplate&output_name={malicious_output}',
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
            with patch('routes.report_generation.GenerateReportFromVV') as mock_generate:
                mock_generated_path = f"C:\\VibrationVIEW\\Reports\\output_{template_name.replace(' ', '_')}.pdf"
                mock_generate.return_value = mock_generated_path

                # Mock file content for this template
                mock_file_content = f"Mock PDF content for {template_name}".encode('utf-8')
                import base64
                mock_base64_content = base64.b64encode(mock_file_content).decode('utf-8')

                with patch('os.path.exists') as mock_exists, \
                     patch('os.path.getsize') as mock_getsize, \
                     patch('builtins.open', create=True) as mock_open:

                    mock_exists.return_value = True
                    mock_getsize.return_value = len(mock_file_content)

                    # Mock file reading
                    mock_file = MagicMock()
                    mock_file.read.return_value = mock_file_content
                    mock_open.return_value.__enter__.return_value = mock_file

                    response = client.post(
                        f'/api/generatereport?template_name={template_name}&output_name=output.pdf',
                        data=vrd_content,
                        headers={
                            'Content-Length': str(len(vrd_content)),
                            'Content-Type': 'application/octet-stream'
                        }
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['success'] is True
                    assert data['data']['template_name'] == template_name

                    # Verify file content is included
                    assert 'content' in data['data']
                    assert data['data']['content'] == mock_base64_content

                    # Save the generated file content to logs folder
                    try:
                        # Get project root (two levels up from test file)
                        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        logs_dir = os.path.join(project_root, "logs")
                        os.makedirs(logs_dir, exist_ok=True)

                        # Save the mock file content
                        safe_template_name = template_name.replace(' ', '_').replace('.', '_')
                        saved_filename = f"test_output_multiple_{safe_template_name}.pdf"
                        saved_path = os.path.join(logs_dir, saved_filename)

                        with open(saved_path, 'wb') as f:
                            f.write(mock_file_content)

                        print(f"Saved test output for {template_name} to: {saved_path} ({len(mock_file_content)} bytes)")

                    except Exception as e:
                        print(f"Failed to save test output for {template_name} to logs: {e}")

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

        with patch('routes.report_generation.GenerateReportFromVV') as mock_generate:
            mock_generated_path = "C:\\VibrationVIEW\\Reports\\test_report_2025-09-22_final.pdf"
            mock_generate.return_value = mock_generated_path

            # Mock file content with special characters
            mock_file_content = f"Mock PDF content for special chars test: {template_name} -> {output_name}".encode('utf-8')
            import base64
            mock_base64_content = base64.b64encode(mock_file_content).decode('utf-8')

            with patch('os.path.exists') as mock_exists, \
                 patch('os.path.getsize') as mock_getsize, \
                 patch('builtins.open', create=True) as mock_open:

                mock_exists.return_value = True
                mock_getsize.return_value = len(mock_file_content)

                # Mock file reading
                mock_file = MagicMock()
                mock_file.read.return_value = mock_file_content
                mock_open.return_value.__enter__.return_value = mock_file

                response = client.post(
                    f'/api/generatereport?template_name={template_name}&output_name={output_name}',
                    data=vrd_content,
                    headers={
                        'Content-Length': str(len(vrd_content)),
                        'Content-Type': 'application/octet-stream'
                    }
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
                assert data['data']['template_name'] == template_name
                assert data['data']['output_name'] == output_name

                # Verify file content is included
                assert 'content' in data['data']
                assert data['data']['content'] == mock_base64_content

                # Save the generated file content to logs folder
                try:
                    # Get project root (two levels up from test file)
                    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    logs_dir = os.path.join(project_root, "logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    # Save the mock file content with safe filename
                    safe_filename = f"test_output_special_chars_{output_name.replace('-', '_').replace('.', '_')}.pdf"
                    saved_path = os.path.join(logs_dir, safe_filename)

                    with open(saved_path, 'wb') as f:
                        f.write(mock_file_content)

                    print(f"Saved test output for special chars test to: {saved_path} ({len(mock_file_content)} bytes)")

                except Exception as e:
                    print(f"Failed to save test output for special chars test to logs: {e}")