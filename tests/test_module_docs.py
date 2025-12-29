# ============================================================================
# FILE: tests/test_module_docs.py
# ============================================================================

"""
Tests to verify each route module includes a get_documentation endpoint
"""

import pytest
import json
from app import set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW


# All route modules that should have documentation endpoints
ROUTE_MODULES = [
    'advanced_control',
    'advanced_control_sine',
    'advanced_control_system_check',
    'auxinputs',
    'basic_control',
    'data_retrieval',
    'gui_control',
    'hardware_config',
    'input_config',
    'log',
    'recording',
    'report_generation',
    'reporting',
    'status_properties',
    'teds',
    'vectors_legacy',
    'virtual_channels',
]


class TestModuleDocumentation:
    """Test that each module has a documentation endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    @pytest.mark.parametrize("module_name", ROUTE_MODULES)
    def test_module_has_docs_endpoint(self, client, module_name):
        """Test that each module has a /docs/{module} endpoint"""
        response = client.get(f'/api/v1/docs/{module_name}')

        assert response.status_code == 200, f"Module '{module_name}' missing docs endpoint"
        data = json.loads(response.data)

        # Verify basic documentation structure
        assert 'module' in data or 'endpoints' in data, \
            f"Module '{module_name}' docs missing 'module' or 'endpoints' key"

    @pytest.mark.parametrize("module_name", ROUTE_MODULES)
    def test_module_docs_has_endpoints(self, client, module_name):
        """Test that each module's docs includes endpoints information"""
        response = client.get(f'/api/v1/docs/{module_name}')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'endpoints' in data, \
            f"Module '{module_name}' docs missing 'endpoints' section"
        assert isinstance(data['endpoints'], dict), \
            f"Module '{module_name}' endpoints should be a dictionary"
        assert len(data['endpoints']) > 0, \
            f"Module '{module_name}' has no documented endpoints"

    @pytest.mark.parametrize("module_name", ROUTE_MODULES)
    def test_module_docs_has_module_name(self, client, module_name):
        """Test that each module's docs includes its module name"""
        response = client.get(f'/api/v1/docs/{module_name}')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert 'module' in data, \
            f"Module '{module_name}' docs missing 'module' field"
        assert data['module'] == module_name, \
            f"Module '{module_name}' has wrong module name: {data.get('module')}"


class TestMainDocsEndpoint:
    """Test the main /docs endpoint"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def test_main_docs_endpoint_exists(self, client):
        """Test that /docs endpoint exists"""
        response = client.get('/api/v1/docs')

        assert response.status_code == 200
        data = json.loads(response.data)
        # Main docs should have some content
        assert len(data) > 0


class TestDocumentationContent:
    """Test documentation content quality"""

    def setup_method(self):
        """Setup for each test method"""
        reset_vv_instance()
        self.mock_instance = MockVibrationVIEW()
        set_vv_instance(self.mock_instance)

    def teardown_method(self):
        """Cleanup after each test method"""
        reset_vv_instance()

    def _is_endpoint_definition(self, endpoint_info):
        """Check if this is an endpoint definition (has description) vs a grouping header"""
        if isinstance(endpoint_info, str):
            # Simple format: 'GET /endpoint': 'description string'
            return True
        if not isinstance(endpoint_info, dict):
            return False
        # Endpoint definitions have 'description' key
        # Grouping headers contain nested endpoint definitions (dicts with 'description')
        return 'description' in endpoint_info

    def _get_all_endpoints(self, endpoints_dict):
        """Recursively get all endpoint definitions from potentially nested structure"""
        all_endpoints = []
        for name, info in endpoints_dict.items():
            if isinstance(info, str):
                # Simple format: endpoint name -> description string
                all_endpoints.append((name, {'description': info}))
            elif isinstance(info, dict):
                if self._is_endpoint_definition(info):
                    all_endpoints.append((name, info))
                else:
                    # This is a grouping header - recurse into nested endpoints
                    all_endpoints.extend(self._get_all_endpoints(info))
        return all_endpoints

    @pytest.mark.parametrize("module_name", ROUTE_MODULES)
    def test_endpoint_docs_have_description(self, client, module_name):
        """Test that documented endpoints have descriptions"""
        response = client.get(f'/api/v1/docs/{module_name}')

        assert response.status_code == 200
        data = json.loads(response.data)

        if 'endpoints' in data:
            endpoints = self._get_all_endpoints(data['endpoints'])
            assert len(endpoints) > 0, \
                f"Module '{module_name}' has no endpoint definitions"

            for endpoint_name, endpoint_info in endpoints:
                assert 'description' in endpoint_info, \
                    f"Endpoint '{endpoint_name}' in module '{module_name}' missing description"

    def test_all_modules_accessible(self, client):
        """Test that all module docs are accessible in one pass"""
        failed_modules = []
        for module_name in ROUTE_MODULES:
            response = client.get(f'/api/v1/docs/{module_name}')
            if response.status_code != 200:
                failed_modules.append(module_name)

        assert len(failed_modules) == 0, \
            f"The following modules are missing docs endpoints: {failed_modules}"
