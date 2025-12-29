# ============================================================================
# FILE: tests/test_reporting.py
# ============================================================================

"""
Tests for reporting routes (/reportfield, /reportfields, /reportfieldshistory, etc.)
"""

import pytest
import json
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


class TestReportField:
    """Test /reportfield endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_reportfield_with_field_parameter(self, client):
        """Test GET /reportfield?field=TestName"""
        self.mock_instance.ReportField.return_value = "My Test Name"

        response = client.get('/api/v1/reportfield?field=TestName')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == "My Test Name"
        assert data['data']['field'] == "TestName"
        assert data['data']['executed'] is True
        self.mock_instance.ReportField.assert_called_once_with('TestName')

    def test_reportfield_unnamed_parameter(self, client):
        """Test GET /reportfield?TestName (unnamed parameter syntax)"""
        self.mock_instance.ReportField.return_value = "My Test Name"

        response = client.get('/api/v1/reportfield?TestName')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == "My Test Name"
        assert data['data']['field'] == "TestName"
        self.mock_instance.ReportField.assert_called_once_with('TestName')

    def test_reportfield_missing_parameter(self, client):
        """Test GET /reportfield with no parameters returns 400"""
        response = client.get('/api/v1/reportfield')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_reportfield_empty_result(self, client):
        """Test GET /reportfield when field returns empty string"""
        self.mock_instance.ReportField.return_value = ""

        response = client.get('/api/v1/reportfield?field=EmptyField')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == ""

    def test_reportfield_numeric_result(self, client):
        """Test GET /reportfield when field returns numeric value"""
        self.mock_instance.ReportField.return_value = "123.456"

        response = client.get('/api/v1/reportfield?field=RunTime')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == "123.456"

    def test_reportfield_special_characters(self, client):
        """Test GET /reportfield with field containing special characters"""
        self.mock_instance.ReportField.return_value = "Value with special chars: <>&\""

        response = client.get('/api/v1/reportfield?field=SpecialField')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == "Value with special chars: <>&\""

    def test_reportfield_common_fields(self, client):
        """Test common report field names"""
        common_fields = [
            ('TestName', 'Random Vibration Test'),
            ('StartTime', '2025-01-15 10:30:00'),
            ('StopCode', 'Stop Button Pressed'),
            ('RunTime', '01:00:00'),
            ('LastDataFile', 'C:\\Data\\test.vrd'),
        ]

        for field_name, expected_value in common_fields:
            self.mock_instance.ReportField.return_value = expected_value

            response = client.get(f'/api/v1/reportfield?field={field_name}')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['result'] == expected_value
            assert data['data']['field'] == field_name


class TestReportFields:
    """Test /reportfields endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_reportfields_get_multiple_fields(self, client):
        """Test GET /reportfields?TestName&StartTime&RunTime"""
        self.mock_instance.ReportFields = lambda fields: ['Test1', '2025-01-15', '3600']

        response = client.get('/api/v1/reportfields?TestName&StartTime&RunTime')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == ['Test1', '2025-01-15', '3600']
        assert data['data']['fields_string'] == 'TestName,StartTime,RunTime'

    def test_reportfields_get_with_fields_param(self, client):
        """Test GET /reportfields?fields=TestName,StartTime"""
        self.mock_instance.ReportFields = lambda fields: ['Test1', '2025-01-15']

        response = client.get('/api/v1/reportfields?fields=TestName,StartTime')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['fields_string'] == 'TestName,StartTime'

    def test_reportfields_post_string(self, client):
        """Test POST /reportfields with comma-delimited string"""
        self.mock_instance.ReportFields = lambda fields: ['Test1', '2025-01-15', '3600']

        response = client.post(
            '/api/v1/reportfields',
            json={'fields': 'TestName,StartTime,RunTime'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == ['Test1', '2025-01-15', '3600']

    def test_reportfields_post_array(self, client):
        """Test POST /reportfields with array of fields"""
        self.mock_instance.ReportFields = lambda fields: ['Test1', '2025-01-15']

        response = client.post(
            '/api/v1/reportfields',
            json={'fields': ['TestName', 'StartTime']}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['fields_string'] == 'TestName,StartTime'

    def test_reportfields_missing_fields(self, client):
        """Test /reportfields with no fields returns 400"""
        response = client.get('/api/v1/reportfields')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_reportfields_empty_fields(self, client):
        """Test POST /reportfields with empty fields"""
        response = client.post(
            '/api/v1/reportfields',
            json={'fields': ''}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_reportfields_wildcard(self, client):
        """Test /reportfields with wildcard suffix"""
        self.mock_instance.ReportFields = lambda fields: [['1.0', '2.0', '3.0', '4.0']]

        response = client.get('/api/v1/reportfields?ChAccelRMS*|')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'ChAccelRMS*|' in data['data']['fields_string']


class TestReportFieldsHistory:
    """Test /reportfieldshistory endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_reportfieldshistory_get(self, client):
        """Test GET /reportfieldshistory?StopCode&RunTime&Time"""
        mock_results = [
            ['StopCode', 'Starting', 'Running', 'Stop Button Pressed'],
            ['RunTime', '00:00:00', '01:00:00', '02:00:00'],
            ['Time', '10:00:00', '11:00:00', '12:00:00']
        ]
        self.mock_instance.ReportFieldsHistory.return_value = mock_results

        response = client.get('/api/v1/reportfieldshistory?StopCode&RunTime&Time')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == mock_results
        assert data['data']['fields_string'] == 'StopCode,RunTime,Time'

    def test_reportfieldshistory_post_string(self, client):
        """Test POST /reportfieldshistory with string"""
        mock_results = [['StopCode', 'Stop Button Pressed']]
        self.mock_instance.ReportFieldsHistory.return_value = mock_results

        response = client.post(
            '/api/v1/reportfieldshistory',
            json={'fields': 'StopCode'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_reportfieldshistory_post_array(self, client):
        """Test POST /reportfieldshistory with array"""
        mock_results = [['StopCode', 'Running', 'Stop Button Pressed'], ['RunTime', '01:00:00', '02:00:00']]
        self.mock_instance.ReportFieldsHistory.return_value = mock_results

        response = client.post(
            '/api/v1/reportfieldshistory',
            json={'fields': ['StopCode', 'RunTime']}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['fields_string'] == 'StopCode,RunTime'

    def test_reportfieldshistory_missing_fields(self, client):
        """Test /reportfieldshistory with no fields returns 400"""
        response = client.get('/api/v1/reportfieldshistory')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_reportfieldshistory_no_data(self, client):
        """Test /reportfieldshistory when no data files available"""
        from pywintypes import com_error
        from utils.vv_error_codes import VVIEW_E_NO_DATA
        # Simulate VVIEW_E_NO_DATA error - scode at index 5
        error = com_error(-2147352567, 'Exception occurred.', (0, None, 'No data', None, 0, VVIEW_E_NO_DATA), None)
        self.mock_instance.ReportFieldsHistory.side_effect = error

        response = client.get('/api/v1/reportfieldshistory?StopCode')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == []
        assert 'No saved data files available' in data['message']

    def test_reportfieldshistory_test_running(self, client):
        """Test /reportfieldshistory when test is running"""
        from pywintypes import com_error
        from utils.vv_error_codes import VVIEW_E_ALREADY_RUNNING
        # Simulate VVIEW_E_ALREADY_RUNNING error - scode at index 5
        error = com_error(-2147352567, 'Exception occurred.', (0, None, 'Already running', None, 0, VVIEW_E_ALREADY_RUNNING), None)
        self.mock_instance.ReportFieldsHistory.side_effect = error

        response = client.get('/api/v1/reportfieldshistory?StopCode')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == []
        assert 'History not available while test is running' in data['message']


class TestReportVector:
    """Test /reportvector endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_reportvector_get(self, client):
        """Test GET /reportvector?Frequency&Demand"""
        mock_result = [[10.0, 20.0, 30.0], [1.0, 2.0, 3.0]]
        self.mock_instance.ReportVector = lambda vectors: mock_result

        response = client.get('/api/v1/reportvector?Frequency&Demand')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == mock_result
        assert data['data']['vectors'] == 'Frequency,Demand'

    def test_reportvector_post_string(self, client):
        """Test POST /reportvector with string"""
        mock_result = [[10.0, 20.0]]
        self.mock_instance.ReportVector = lambda vectors: mock_result

        response = client.post(
            '/api/v1/reportvector',
            json={'vectors': 'Frequency'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

    def test_reportvector_post_array(self, client):
        """Test POST /reportvector with array"""
        mock_result = [[10.0, 20.0], [1.0, 2.0]]
        self.mock_instance.ReportVector = lambda vectors: mock_result

        response = client.post(
            '/api/v1/reportvector',
            json={'vectors': ['Frequency', 'Demand']}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['vectors'] == 'Frequency,Demand'

    def test_reportvector_missing_vectors(self, client):
        """Test /reportvector with no vectors returns 400"""
        response = client.get('/api/v1/reportvector')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'


class TestReportVectorHeader:
    """Test /reportvectorheader endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_reportvectorheader_get(self, client):
        """Test GET /reportvectorheader?Frequency&Demand"""
        mock_result = ['Hz', 'g']
        self.mock_instance.ReportVectorHeader = lambda vectors: mock_result

        response = client.get('/api/v1/reportvectorheader?Frequency&Demand')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] == mock_result

    def test_reportvectorheader_missing_vectors(self, client):
        """Test /reportvectorheader with no vectors returns 400"""
        response = client.get('/api/v1/reportvectorheader')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'


class TestFormFields:
    """Test /formfields endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_formfields_get(self, client):
        """Test GET /formfields returns all form fields"""
        mock_results = [
            ['Customer', 'ACME Corp'],
            ['PartNumber', '12345'],
            ['SerialNumber', 'SN-001']
        ]
        self.mock_instance.FormFields = lambda: mock_results

        response = client.get('/api/v1/formfields')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == mock_results
        assert '3 fields returned' in data['message']

    def test_formfields_get_empty(self, client):
        """Test GET /formfields when no form data"""
        from pywintypes import com_error
        from utils.vv_error_codes import VVIEW_E_NO_DATA
        # Simulate VVIEW_E_NO_DATA error - scode at index 5
        error = com_error(-2147352567, 'Exception occurred.', (0, None, 'No data', None, 0, VVIEW_E_NO_DATA), None)
        self.mock_instance.FormFields = lambda: (_ for _ in ()).throw(error)

        response = client.get('/api/v1/formfields')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['results'] == []
        assert 'No form data available' in data['message']

    def test_formfields_post_json(self, client):
        """Test POST /formfields with JSON body"""
        self.mock_instance.PostFormFields = lambda fields: True

        response = client.post(
            '/api/v1/formfields',
            json={'fields': [['Customer', 'ACME Corp'], ['PartNumber', '12345']]}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['result'] is True
        assert data['data']['fields_count'] == 2

    def test_formfields_post_form_data(self, client):
        """Test POST /formfields with multipart/form-data"""
        self.mock_instance.PostFormFields = lambda fields: True

        response = client.post(
            '/api/v1/formfields',
            data={'Customer': 'ACME Corp', 'PartNumber': '12345'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['fields_count'] == 2

    def test_formfields_post_missing_fields(self, client):
        """Test POST /formfields with no fields returns 400"""
        response = client.post(
            '/api/v1/formfields',
            json={}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'

    def test_formfields_post_invalid_format(self, client):
        """Test POST /formfields with invalid fields format returns 400"""
        response = client.post(
            '/api/v1/formfields',
            json={'fields': 'not an array'}
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'INVALID_PARAMETER'

    def test_formfields_put(self, client):
        """Test PUT /formfields works same as POST"""
        self.mock_instance.PostFormFields = lambda fields: True

        response = client.put(
            '/api/v1/formfields',
            json={'fields': [['Customer', 'ACME Corp']]}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestReportingDocs:
    """Test /docs/reporting endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_docs_reporting(self, client):
        """Test GET /docs/reporting returns documentation"""
        response = client.get('/api/v1/docs/reporting')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['module'] == 'reporting'
        assert 'endpoints' in data
        assert 'GET /reportfield' in data['endpoints']
        assert 'GET|POST /reportfields' in data['endpoints']
        assert 'GET|POST /reportfieldshistory' in data['endpoints']
        assert 'GET|POST /reportvector' in data['endpoints']
        assert 'GET /formfields' in data['endpoints']
        assert 'POST|PUT /formfields' in data['endpoints']
