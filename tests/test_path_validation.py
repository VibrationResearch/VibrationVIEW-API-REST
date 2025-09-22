# ============================================================================
# FILE: tests/test_path_validation.py (Path Validation Security Tests) - v1
# ============================================================================

"""
Test cases for path validation security functionality
Ensures that file path restrictions prevent path traversal attacks
"""

import pytest
from pathlib import Path
from unittest.mock import patch

from utils.path_validator import (
    PathValidationError,
    get_authorized_directories,
    normalize_path,
    is_path_within_authorized_directories,
    validate_file_path,
    validate_output_path,
    secure_path_join
)
from config import Config


class TestPathValidation:
    """Test path validation utility functions"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration with test directories"""
        with patch.object(Config, 'REPORT_FOLDER', 'C:\\VibrationVIEW\\Reports'), \
             patch.object(Config, 'PROFILE_FOLDER', 'C:\\VibrationVIEW\\Profiles'), \
             patch.object(Config, 'DATA_FOLDER', 'C:\\VibrationVIEW\\Data'):
            yield

    def test_get_authorized_directories(self, mock_config):
        """Test getting authorized directories from config"""
        directories = get_authorized_directories()
        expected = [
            'C:\\VibrationVIEW\\Reports',
            'C:\\VibrationVIEW\\Profiles',
            'C:\\VibrationVIEW\\Data'
        ]
        assert set(directories) == set(expected)

    def test_normalize_path(self):
        """Test path normalization"""
        # Test relative path resolution
        current_dir = Path.cwd()
        normalized = normalize_path("./test.txt")
        expected = current_dir / "test.txt"
        assert normalized == expected

        # Test absolute path
        abs_path = Path("C:\\test\\file.txt")
        normalized = normalize_path(abs_path)
        assert normalized == abs_path.resolve()

    def test_is_path_within_authorized_directories_valid(self, mock_config):
        """Test valid paths within authorized directories"""
        # Test file in REPORT_FOLDER
        valid_path = "C:\\VibrationVIEW\\Reports\\test.pdf"
        assert is_path_within_authorized_directories(valid_path)

        # Test file in subdirectory of PROFILE_FOLDER
        valid_subdir_path = "C:\\VibrationVIEW\\Profiles\\subdir\\test.vrd"
        assert is_path_within_authorized_directories(valid_subdir_path)

        # Test file in DATA_FOLDER
        valid_data_path = "C:\\VibrationVIEW\\Data\\measurements\\data.txt"
        assert is_path_within_authorized_directories(valid_data_path)

    def test_is_path_within_authorized_directories_invalid(self, mock_config):
        """Test invalid paths outside authorized directories"""
        # Test path outside authorized directories
        invalid_path = "C:\\Windows\\System32\\evil.exe"
        assert not is_path_within_authorized_directories(invalid_path)

        # Test path traversal attempt
        traversal_path = "C:\\VibrationVIEW\\Reports\\..\\..\\Windows\\System32\\evil.exe"
        assert not is_path_within_authorized_directories(traversal_path)

        # Test completely different drive
        different_drive = "D:\\malicious\\file.txt"
        assert not is_path_within_authorized_directories(different_drive)

    def test_validate_file_path_success(self, mock_config):
        """Test successful file path validation"""
        valid_path = "C:\\VibrationVIEW\\Reports\\test.pdf"
        result = validate_file_path(valid_path, "test operation")
        # Should return normalized path
        assert result == str(normalize_path(valid_path))

    def test_validate_file_path_empty(self, mock_config):
        """Test validation with empty path"""
        with pytest.raises(PathValidationError, match="Empty file path not allowed"):
            validate_file_path("", "test operation")

        with pytest.raises(PathValidationError, match="Empty file path not allowed"):
            validate_file_path(None, "test operation")

    def test_validate_file_path_traversal_detection(self, mock_config):
        """Test detection of path traversal attempts"""
        # Test basic path traversal
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validate_file_path("C:\\VibrationVIEW\\Reports\\..\\..\\Windows\\System32\\evil.exe", "test")

        # Test relative traversal
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validate_file_path("../../../etc/passwd", "test")

        # Test colon in middle of path (Windows drive letter detection)
        with pytest.raises(PathValidationError, match="Path traversal detected"):
            validate_file_path("C:\\VibrationVIEW\\Reports\\C:\\Windows\\evil.exe", "test")

    def test_validate_file_path_unauthorized_directory(self, mock_config):
        """Test validation with unauthorized directory"""
        unauthorized_path = "C:\\Windows\\System32\\evil.exe"
        with pytest.raises(PathValidationError, match="not within authorized directories"):
            validate_file_path(unauthorized_path, "test operation")

    def test_validate_output_path_filename_only(self, mock_config):
        """Test output path validation with filename only"""
        # Should place in REPORT_FOLDER
        result = validate_output_path("test.pdf", "test operation")
        expected = str(normalize_path("C:\\VibrationVIEW\\Reports\\test.pdf"))
        assert result == expected

    def test_validate_output_path_full_path(self, mock_config):
        """Test output path validation with full path"""
        # Valid full path in authorized directory
        full_path = "C:\\VibrationVIEW\\Reports\\subdir\\test.pdf"
        result = validate_output_path(full_path, "test operation")
        assert result == str(normalize_path(full_path))

    def test_validate_output_path_unauthorized(self, mock_config):
        """Test output path validation with unauthorized path"""
        unauthorized_path = "C:\\Windows\\System32\\evil.exe"
        with pytest.raises(PathValidationError, match="not within authorized directories"):
            validate_output_path(unauthorized_path, "test operation")

    def test_validate_output_path_no_report_folder(self):
        """Test output path validation when REPORT_FOLDER not configured"""
        with patch.object(Config, 'REPORT_FOLDER', None):
            with pytest.raises(PathValidationError, match="No REPORT_FOLDER configured"):
                validate_output_path("test.pdf", "test operation")

    def test_secure_path_join_success(self):
        """Test secure path joining within base directory"""
        base_dir = "C:\\VibrationVIEW\\Reports"
        result = secure_path_join(base_dir, "subdir", "test.pdf")
        expected = str(normalize_path("C:\\VibrationVIEW\\Reports\\subdir\\test.pdf"))
        assert result == expected

    def test_secure_path_join_traversal_prevention(self):
        """Test secure path join prevents directory traversal"""
        base_dir = "C:\\VibrationVIEW\\Reports"

        # Should prevent escaping base directory
        with pytest.raises(PathValidationError, match="would escape base directory"):
            secure_path_join(base_dir, "..", "..", "Windows", "System32", "evil.exe")

    def test_secure_path_join_multiple_components(self):
        """Test secure path join with multiple components"""
        base_dir = "C:\\VibrationVIEW\\Reports"
        result = secure_path_join(base_dir, "year2024", "month01", "day15", "report.pdf")
        expected = str(normalize_path("C:\\VibrationVIEW\\Reports\\year2024\\month01\\day15\\report.pdf"))
        assert result == expected


class TestReportGenerationSecurity:
    """Test security aspects of report generation endpoints"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        with patch.object(Config, 'REPORT_FOLDER', 'C:\\VibrationVIEW\\Reports'), \
             patch.object(Config, 'PROFILE_FOLDER', 'C:\\VibrationVIEW\\Profiles'), \
             patch.object(Config, 'DATA_FOLDER', 'C:\\VibrationVIEW\\Data'):
            yield

    def test_path_validation_integration(self, mock_config):
        """Test integration of path validation with report generation functions"""
        from routes.report_generation import validate_file_path, validate_output_path

        # Test valid paths
        valid_input = "C:\\VibrationVIEW\\Data\\test.vrd"
        valid_output = "report.pdf"

        # These should not raise exceptions
        validated_input = validate_file_path(valid_input, "report generation")
        validated_output = validate_output_path(valid_output, "report generation")

        assert validated_input == str(normalize_path(valid_input))
        assert validated_output == str(normalize_path("C:\\VibrationVIEW\\Reports\\report.pdf"))

    def test_security_error_responses(self, mock_config):
        """Test that security violations return appropriate error responses"""
        # Test with malicious paths that should be rejected
        malicious_paths = [
            "C:\\Windows\\System32\\evil.exe",
            "../../../etc/passwd",
            "C:\\VibrationVIEW\\Reports\\..\\..\\Windows\\System32\\cmd.exe"
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(PathValidationError):
                validate_file_path(malicious_path, "test operation")

    @pytest.mark.unit
    def test_path_validation_edge_cases(self, mock_config):
        """Test edge cases in path validation"""
        # Test empty string
        with pytest.raises(PathValidationError):
            validate_file_path("", "test")

        # Test None
        with pytest.raises(PathValidationError):
            validate_file_path(None, "test")

        # Test whitespace only
        with pytest.raises(PathValidationError):
            validate_file_path("   ", "test")

    @pytest.mark.unit
    def test_directory_configuration_edge_cases(self):
        """Test behavior when directories are not configured"""
        # Test when no directories are configured
        with patch.object(Config, 'REPORT_FOLDER', None), \
             patch.object(Config, 'PROFILE_FOLDER', None), \
             patch.object(Config, 'DATA_FOLDER', None):

            directories = get_authorized_directories()
            assert directories == []

            # Should reject any path when no authorized directories
            assert not is_path_within_authorized_directories("C:\\any\\path\\file.txt")

    def test_case_sensitivity(self, mock_config):
        """Test path validation is case-insensitive on Windows"""
        # These should be treated as the same on Windows
        lower_case = "c:\\vibrationview\\reports\\test.pdf"
        upper_case = "C:\\VIBRATIONVIEW\\REPORTS\\TEST.PDF"
        mixed_case = "C:\\VibrationView\\Reports\\Test.PDF"

        # All should be valid (case-insensitive on Windows)
        assert is_path_within_authorized_directories(lower_case)
        assert is_path_within_authorized_directories(upper_case)
        assert is_path_within_authorized_directories(mixed_case)