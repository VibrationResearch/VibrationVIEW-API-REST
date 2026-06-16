# ============================================================================
# FILE: tests/test_vv_error_codes.py (VV Error Code Classification Tests)
# ============================================================================

"""
Test cases for VibrationVIEW error code classification and the
handle_errors decorator's integration with vv_error_codes.
"""

import pytest

from utils.vv_error_codes import (
    VVIEW_E_ACTIVEX_KEYMISSING,
    VVIEW_E_ALREADY_RUNNING,
    VVIEW_E_BADPARAMETER,
    VVIEW_E_CANT_CREATE_FILE,
    VVIEW_E_DATABASE_NOT_AVAILABLE,
    VVIEW_E_FILE_EXISTS,
    VVIEW_E_KEY_NOT_FOUND,
    VVIEW_E_LENGTH_MISMATCH,
    VVIEW_E_NO_DATA,
    VVIEW_E_NO_SUCH_DIRECTORY,
    VVIEW_E_RECORDING,
    VVIEW_E_TEST_NOT_FOUND,
    VVIEW_E_UNEXPECTED,
    VVIEW_E_WAITING_FOR_BOX,
    VVIEW_E_WRONGTESTMODE,
    VVIEW_S_NOT_RUNNING,
    VVIEW_S_SHORTER_THAN_REQUESTED,
    classify_vview_error,
    get_error_info,
    get_scode_from_exception,
    is_vview_error,
)


class TestClassifyVviewError:
    """Test classify_vview_error returns correct (http_status, error_code, message)"""

    @pytest.mark.parametrize(
        "scode, expected_status, expected_code",
        [
            # 400 - Bad Request
            (VVIEW_E_BADPARAMETER, 400, "BAD_PARAMETER"),
            (VVIEW_E_LENGTH_MISMATCH, 400, "LENGTH_MISMATCH"),
            # 403 - Forbidden (licensing)
            (VVIEW_E_ACTIVEX_KEYMISSING, 403, "LICENSE_ERROR"),
            # 404 - Not Found
            (VVIEW_E_TEST_NOT_FOUND, 404, "TEST_NOT_FOUND"),
            (VVIEW_E_KEY_NOT_FOUND, 404, "KEY_NOT_FOUND"),
            (VVIEW_E_NO_SUCH_DIRECTORY, 404, "DIRECTORY_NOT_FOUND"),
            (VVIEW_E_NO_DATA, 404, "NO_DATA"),
            # 409 - Conflict
            (VVIEW_E_ALREADY_RUNNING, 409, "ALREADY_RUNNING"),
            (VVIEW_E_RECORDING, 409, "ALREADY_RECORDING"),
            (VVIEW_E_WRONGTESTMODE, 409, "WRONG_TEST_MODE"),
            (VVIEW_E_FILE_EXISTS, 409, "FILE_EXISTS"),
            (VVIEW_S_NOT_RUNNING, 409, "NOT_RUNNING"),
            # 500 - Server Error
            (VVIEW_E_CANT_CREATE_FILE, 500, "FILE_CREATE_ERROR"),
            (VVIEW_E_UNEXPECTED, 500, "UNEXPECTED_ERROR"),
            # 503 - Service Unavailable
            (VVIEW_E_DATABASE_NOT_AVAILABLE, 503, "DATABASE_UNAVAILABLE"),
            (VVIEW_E_WAITING_FOR_BOX, 503, "HARDWARE_NOT_READY"),
        ],
    )
    def test_known_error_codes(self, scode, expected_status, expected_code):
        http_status, error_code, message = classify_vview_error(scode)
        assert http_status == expected_status
        assert error_code == expected_code
        assert isinstance(message, str) and len(message) > 0

    def test_success_severity_shorter_than_requested(self):
        http_status, error_code, _ = classify_vview_error(VVIEW_S_SHORTER_THAN_REQUESTED)
        assert http_status == 200
        assert error_code == "SHORTER_THAN_REQUESTED"

    def test_unknown_scode_returns_500(self):
        http_status, error_code, message = classify_vview_error(-9999999)
        assert http_status == 500
        assert error_code == "COM_ERROR"
        assert "-9999999" in message


class TestGetScodeFromException:
    """Test scode extraction from COM-style exceptions"""

    def _make_com_exception(self, scode):
        """Create a fake COM exception with scode at args[2][5]"""
        exc = Exception(
            "COM error",
            "description",
            (None, None, None, None, None, scode),
        )
        return exc

    def test_extracts_scode(self):
        exc = self._make_com_exception(VVIEW_E_ALREADY_RUNNING)
        assert get_scode_from_exception(exc) == VVIEW_E_ALREADY_RUNNING

    def test_returns_none_for_short_args(self):
        exc = Exception("only one arg")
        assert get_scode_from_exception(exc) is None

    def test_returns_none_for_non_tuple_excinfo(self):
        exc = Exception("a", "b", "not a tuple")
        assert get_scode_from_exception(exc) is None


class TestIsVviewError:
    """Test is_vview_error matching"""

    def _make_com_exception(self, scode):
        return Exception("err", "desc", (None, None, None, None, None, scode))

    def test_matches_correct_code(self):
        exc = self._make_com_exception(VVIEW_E_NO_DATA)
        assert is_vview_error(exc, VVIEW_E_NO_DATA) is True

    def test_does_not_match_wrong_code(self):
        exc = self._make_com_exception(VVIEW_E_NO_DATA)
        assert is_vview_error(exc, VVIEW_E_ALREADY_RUNNING) is False

    def test_plain_exception_does_not_match(self):
        exc = Exception("plain")
        assert is_vview_error(exc, VVIEW_E_NO_DATA) is False


class TestGetErrorInfo:
    """Test get_error_info returns code and human-readable name"""

    def _make_com_exception(self, scode):
        return Exception("err", "desc", (None, None, None, None, None, scode))

    def test_known_code_returns_info(self):
        exc = self._make_com_exception(VVIEW_E_BADPARAMETER)
        info = get_error_info(exc)
        assert info is not None
        assert info["code"] == VVIEW_E_BADPARAMETER
        assert "parameter" in info["name"].lower()

    def test_unknown_code_returns_info_with_unknown_name(self):
        exc = self._make_com_exception(-12345)
        info = get_error_info(exc)
        assert info is not None
        assert info["code"] == -12345
        assert "UNKNOWN" in info["name"]

    def test_plain_exception_returns_none(self):
        exc = Exception("no COM info")
        assert get_error_info(exc) is None


class TestHandleErrorsDecorator:
    """Test that handle_errors maps VV errors to correct HTTP responses"""

    @pytest.fixture
    def app(self):
        from app import create_app
        from config import TestingConfig

        app = create_app(TestingConfig)
        return app

    def _make_com_exception(self, scode):
        return Exception("COM err", "desc", (None, None, None, None, None, scode))

    def test_already_running_returns_409(self, app):

        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise self._make_com_exception(VVIEW_E_ALREADY_RUNNING)

        with app.test_request_context():
            response, status = fake_endpoint()
            assert status == 409

    def test_bad_parameter_returns_400(self, app):
        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise self._make_com_exception(VVIEW_E_BADPARAMETER)

        with app.test_request_context():
            response, status = fake_endpoint()
            assert status == 400

    def test_no_data_returns_404(self, app):
        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise self._make_com_exception(VVIEW_E_NO_DATA)

        with app.test_request_context():
            response, status = fake_endpoint()
            assert status == 404

    def test_database_unavailable_returns_503(self, app):
        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise self._make_com_exception(VVIEW_E_DATABASE_NOT_AVAILABLE)

        with app.test_request_context():
            response, status = fake_endpoint()
            assert status == 503

    def test_unknown_exception_returns_500(self, app):
        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise ValueError("something unexpected") 

        with app.test_request_context():
            response, status = fake_endpoint()
            assert status == 500

    def test_response_contains_error_details(self, app):
        from utils.decorators import handle_errors

        @handle_errors
        def fake_endpoint():
            raise self._make_com_exception(VVIEW_E_TEST_NOT_FOUND)

        with app.test_request_context():
            response, status = fake_endpoint()
            data = response.get_json()
            assert data["success"] is False
            assert data["error"]["code"] == "TEST_NOT_FOUND"
            assert "details" in data["error"]
            assert data["error"]["details"]["code"] == VVIEW_E_TEST_NOT_FOUND
