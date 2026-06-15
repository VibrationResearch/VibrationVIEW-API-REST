# ============================================================================
# FILE: tests/test_system_check_extensions.py
# ============================================================================

"""
Tests to verify all file extensions are recognized as valid
and routed to the correct folders.
"""

import pytest
from unittest.mock import patch
from utils.utils import (
    PROFILE_EXTENSIONS,
    DATA_EXTENSIONS,
    TEMPLATE_EXTENSIONS,
    INPUTCONFIG_EXTENSIONS,
    REPORT_EXTENSIONS,
    ALLOWED_EXTENSIONS,
    get_folder_for_extension,
    handle_binary_upload,
)
from config import Config


# ---- Extension set membership ----

class TestProfileExtensions:
    """All profile extensions should be in PROFILE_EXTENSIONS and ALLOWED_EXTENSIONS."""

    @pytest.mark.parametrize("ext", [
        'vrp', 'vrpj', 'vasor', 'vkp', 'vkpj', 'vsp', 'vspj', 'vdp', 'vdpj', 'vyp',
    ])
    def test_in_profile_extensions(self, ext):
        assert ext in PROFILE_EXTENSIONS

    @pytest.mark.parametrize("ext", [
        'vrp', 'vrpj', 'vasor', 'vkp', 'vkpj', 'vsp', 'vspj', 'vdp', 'vdpj', 'vyp',
    ])
    def test_in_allowed_extensions(self, ext):
        assert ext in ALLOWED_EXTENSIONS

    @pytest.mark.parametrize("ext", [
        'vrp', 'vrpj', 'vasor', 'vkp', 'vkpj', 'vsp', 'vspj', 'vdp', 'vdpj', 'vyp',
    ])
    def test_folder_routing(self, ext):
        assert get_folder_for_extension(ext) == Config.PROFILE_FOLDER
        assert get_folder_for_extension(f'test.{ext}') == Config.PROFILE_FOLDER


class TestDataExtensions:
    """All data extensions should be in DATA_EXTENSIONS and ALLOWED_EXTENSIONS."""

    @pytest.mark.parametrize("ext", ['vrd', 'vkd', 'vsd', 'vdd', 'vyd'])
    def test_in_data_extensions(self, ext):
        assert ext in DATA_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vrd', 'vkd', 'vsd', 'vdd', 'vyd'])
    def test_in_allowed_extensions(self, ext):
        assert ext in ALLOWED_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vrd', 'vkd', 'vsd', 'vdd', 'vyd'])
    def test_folder_routing(self, ext):
        assert get_folder_for_extension(ext) == Config.DATA_FOLDER
        assert get_folder_for_extension(f'test.{ext}') == Config.DATA_FOLDER


class TestTemplateExtensions:
    """All template extensions should be in TEMPLATE_EXTENSIONS and ALLOWED_EXTENSIONS."""

    @pytest.mark.parametrize("ext", ['vsinet', 'vrandomt'])
    def test_in_template_extensions(self, ext):
        assert ext in TEMPLATE_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vsinet', 'vrandomt'])
    def test_in_allowed_extensions(self, ext):
        assert ext in ALLOWED_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vsinet', 'vrandomt'])
    def test_folder_routing(self, ext):
        assert get_folder_for_extension(ext) == Config.NEW_TEST_DEFAULTS_FOLDER
        assert get_folder_for_extension(f'test.{ext}') == Config.NEW_TEST_DEFAULTS_FOLDER


class TestInputConfigExtensions:
    """All input config extensions should be in INPUTCONFIG_EXTENSIONS and ALLOWED_EXTENSIONS."""

    @pytest.mark.parametrize("ext", ['vic', 'vchan', 'inputconfig'])
    def test_in_inputconfig_extensions(self, ext):
        assert ext in INPUTCONFIG_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vic', 'vchan', 'inputconfig'])
    def test_in_allowed_extensions(self, ext):
        assert ext in ALLOWED_EXTENSIONS

    @pytest.mark.parametrize("ext", ['vic', 'vchan', 'inputconfig'])
    def test_folder_routing(self, ext):
        assert get_folder_for_extension(ext) == Config.INPUTCONFIG_FOLDER
        assert get_folder_for_extension(f'test.{ext}') == Config.INPUTCONFIG_FOLDER


class TestReportExtensions:
    """All report extensions should be in REPORT_EXTENSIONS and ALLOWED_EXTENSIONS."""

    @pytest.mark.parametrize("ext", [
        'vvtemplate', 'rtf', 'txt', 'xlsx', 'xlsm', 'xls', 'csv', 'html', 'htm', 'pdf',
    ])
    def test_in_report_extensions(self, ext):
        assert ext in REPORT_EXTENSIONS

    @pytest.mark.parametrize("ext", [
        'vvtemplate', 'rtf', 'txt', 'xlsx', 'xlsm', 'xls', 'csv', 'html', 'htm', 'pdf',
    ])
    def test_in_allowed_extensions(self, ext):
        assert ext in ALLOWED_EXTENSIONS

    @pytest.mark.parametrize("ext", [
        'vvtemplate', 'rtf', 'txt', 'xlsx', 'xlsm', 'xls', 'csv', 'html', 'htm', 'pdf',
    ])
    def test_folder_routing(self, ext):
        assert get_folder_for_extension(ext) == Config.REPORT_FOLDER
        assert get_folder_for_extension(f'test.{ext}') == Config.REPORT_FOLDER


# ---- Binary upload acceptance ----

class TestBinaryUploadAcceptance:
    """handle_binary_upload should accept all allowed extensions and reject unknown ones."""

    @pytest.mark.parametrize("ext,folder_attr", [
        ('vyp', 'PROFILE_FOLDER'),
        ('vrp', 'PROFILE_FOLDER'),
        ('vyd', 'DATA_FOLDER'),
        ('vrd', 'DATA_FOLDER'),
        ('vrandomt', 'NEW_TEST_DEFAULTS_FOLDER'),
        ('vic', 'INPUTCONFIG_FOLDER'),
        ('pdf', 'REPORT_FOLDER'),
    ])
    def test_upload_accepted(self, tmp_path, ext, folder_attr):
        with patch.object(Config, folder_attr, str(tmp_path)):
            result, error, status = handle_binary_upload(f'test.{ext}', b'data')
            assert status == 200
            assert error is None
            assert result['FilePath'].endswith(f'.{ext}')

    def test_upload_rejected_for_unknown_extension(self):
        result, error, status = handle_binary_upload('test.xyz', b'data')
        assert status == 400
        assert result is None
        assert 'Invalid file extension' in error['Error']
