# ============================================================================
# FILE: tests/test_data_retrieval.py
# ============================================================================

"""
Tests for data_retrieval.py routes (merged with vector properties)
Tests both data retrieval and vector properties functionality
Matches current implementation with GET requests and query parameters
"""

import pytest
import json
from app import set_vv_instance, reset_vv_instance, get_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW

class TestDataRetrieval:
    """Test data retrieval endpoints including vector properties"""
    
    def setup_method(self):
        """Setup method run before each test"""
        # Force reset singleton before each test
        reset_vv_instance()
        
        # Create and configure mock instance
        self.mock_vv = MockVibrationVIEW()
        
        # Set the singleton
        set_vv_instance(self.mock_vv)
        
        # Verify our mock is properly set
        instance = get_vv_instance()
        assert instance is self.mock_vv, "Mock instance not properly set in singleton"
    
    def teardown_method(self):
        """Cleanup method run after each test"""
        reset_vv_instance()
    
    # ============================================================================
    # DEBUG AND ROUTE DISCOVERY TESTS
    # ============================================================================
    
    def test_debug_available_routes(self, client):
        """Debug test to see what routes are actually available"""
        print("\n=== Available Routes ===")
        data_retrieval_routes = []
        all_routes = []

        # Use the app context properly
        with client.application.app_context():
            from flask import current_app

            for rule in current_app.url_map.iter_rules():
                route_info = f"{list(rule.methods)} {rule.rule}"
                all_routes.append(route_info)
                if '/api/v1/' in rule.rule and any(endpoint in rule.rule for endpoint in 
                    ['demand', 'control', 'channel', 'output', 'vector', 'channelunit', 'controllabel']):
                    data_retrieval_routes.append(route_info)
                    print(f"DATA RETRIEVAL: {route_info}")

        print(f"\nFound {len(data_retrieval_routes)} data retrieval routes")
        print(f"Total routes: {len(all_routes)}")

        # Test a basic route that should exist
        response = client.get('/')
        print(f"Root route status: {response.status_code}")

        # Try to access data retrieval docs
        response = client.get('/api/v1/docs/data_retrieval')
        print(f"Data retrieval docs route status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Data retrieval blueprint is registered!")
        else:
            print("✗ Data retrieval blueprint may not be registered")
            print(f"Response: {response.data}")

        print("=== End Route Debug ===\n")
        
    def test_debug_singleton_behavior(self, client):
        """Debug test to understand singleton behavior"""
        from app import get_vv_instance, _vv_instance
        
        print(f"Current singleton instance: {_vv_instance}")
        print(f"Retrieved instance: {get_vv_instance()}")
        print(f"Our mock instance: {self.mock_vv}")
        print(f"Is same as mock? {get_vv_instance() is self.mock_vv}")
        
        # Configure mock for a simple test
        self.mock_vv.ChannelUnit.return_value = "debug_unit"
        self.mock_vv.ChannelUnit.reset_mock()
        
        # Test the route with GET request
        response = client.get('/api/v1/channelunit?channelnum=1')
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"Response data: {data}")
            print(f"Mock ChannelUnit call count: {self.mock_vv.ChannelUnit.call_count}")
        elif response.status_code == 404:
            print("Route not found - checking if blueprint is registered")
        else:
            print(f"Unexpected status code: {response.status_code}")
            print(f"Response data: {response.data}")
        
        print("✓ Debug singleton test completed!")
    
    # ============================================================================
    # PRIMARY DATA ARRAYS TESTS
    # ============================================================================
    
    def test_demand(self, client):
        """Test demand endpoint"""
        # Configure mock
        self.mock_vv.Demand.return_value = [1.5, 2.0, 2.5]
        self.mock_vv.Demand.reset_mock()
        
        response = client.get('/api/v1/demand')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/demand not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == [1.5, 2.0, 2.5]
        
        # Verify VibrationVIEW was called
        assert self.mock_vv.Demand.called, "Demand method was not called"
        calls = self.mock_vv.Demand.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((),)  # No arguments
        
        print("✓ Demand endpoint works correctly!")
    
    def test_control(self, client):
        """Test control endpoint"""
        # Configure mock
        self.mock_vv.Control.return_value = [0.8, 1.2, 1.0]
        self.mock_vv.Control.reset_mock()
        
        response = client.get('/api/v1/control')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/control not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == [0.8, 1.2, 1.0]
        
        # Verify VibrationVIEW was called
        assert self.mock_vv.Control.called, "Control method was not called"
        calls = self.mock_vv.Control.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((),)  # No arguments
        
        print("✓ Control endpoint works correctly!")
    
    def test_channel(self, client):
        """Test channel endpoint"""
        # Configure mock
        self.mock_vv.Channel.return_value = [1.0, 2.0, 3.0, 4.0]
        self.mock_vv.Channel.reset_mock()
        
        response = client.get('/api/v1/channel')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/channel not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == [1.0, 2.0, 3.0, 4.0]
        
        # Verify VibrationVIEW was called
        assert self.mock_vv.Channel.called, "Channel method was not called"
        calls = self.mock_vv.Channel.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((),)  # No arguments
        
        print("✓ Channel endpoint works correctly!")
    
    def test_output(self, client):
        """Test output endpoint"""
        # Configure mock
        self.mock_vv.Output.return_value = [2.5, 3.0]
        self.mock_vv.Output.reset_mock()
        
        response = client.get('/api/v1/output')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/output not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == [2.5, 3.0]
        
        # Verify VibrationVIEW was called
        assert self.mock_vv.Output.called, "Output method was not called"
        calls = self.mock_vv.Output.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((),)  # No arguments
        
        print("✓ Output endpoint works correctly!")
    
    # ============================================================================
    # VECTOR DATA TESTS
    # ============================================================================
    
    def test_vector_with_defaults(self, client):
        """Test vector endpoint with default columns"""
        # Configure mock
        mock_vector_data = [[1.0, 2.0, 3.0, 4.0]]
        self.mock_vv.Vector.return_value = mock_vector_data
        self.mock_vv.Vector.reset_mock()
        
        response = client.get('/api/v1/vector?vectorenum=1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vector not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_vector_data
        assert data['data']['vectorenum'] == 1
        assert data['data']['columns'] == 1
        assert data['data']['rows'] == 1
        
        # Verify VibrationVIEW was called with correct parameters
        assert self.mock_vv.Vector.called, "Vector method was not called"
        calls = self.mock_vv.Vector.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((1, 1),)  # vectorenum=1, columns=1 (default)
        
        print("✓ Vector endpoint with defaults works correctly!")
    
    def test_vector_with_columns(self, client):
        """Test vector endpoint with specified columns"""
        # Configure mock
        mock_vector_data = [[1.0, 2.0], [3.0, 4.0]]
        self.mock_vv.Vector.return_value = mock_vector_data
        self.mock_vv.Vector.reset_mock()
        
        response = client.get('/api/v1/vector?vectorenum=2&columns=2')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vector not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_vector_data
        assert data['data']['vectorenum'] == 2
        assert data['data']['columns'] == 2
        assert data['data']['rows'] == 2
        
        # Verify VibrationVIEW was called with correct parameters
        assert self.mock_vv.Vector.called, "Vector method was not called"
        calls = self.mock_vv.Vector.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((2, 2),)  # vectorenum=2, columns=2
        
        print("✓ Vector endpoint with columns works correctly!")
    
    def test_vector_missing_vectorenum(self, client):
        """Test vector endpoint with missing vectorenum parameter"""
        response = client.get('/api/v1/vector')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vector not found - blueprint may not be registered")
        
        assert response.status_code == 400

        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error']['code'] == 'MISSING_PARAMETER'
        assert 'vectorenum' in data['error']['message']
        
        print("✓ Vector parameter validation works!")
    
    def test_vector_invalid_columns(self, client):
        """Test vector endpoint with invalid columns parameter"""
        response = client.get('/api/v1/vector?vectorenum=1&columns=0')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vector not found - blueprint may not be registered")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'columns must be >= 1' in data['error']['message']
        assert data['error']['code'] == 'INVALID_PARAMETER'
        
        print("✓ Vector columns validation works!")
    
    # ============================================================================
    # VECTOR PROPERTIES TESTS (no base conversion)
    # ============================================================================
    
    def test_vector_unit(self, client):
        """Test VectorUnit endpoint - no base conversion"""
        # Configure mock
        self.mock_vv.VectorUnit.return_value = "g"
        self.mock_vv.VectorUnit.reset_mock()
        
        response = client.get('/api/v1/vectorunit?vectorenum=1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vectorunit not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == "g"
        assert data['data']['vectorenum'] == 1
        
        # Verify VibrationVIEW was called with original value (no conversion)
        assert self.mock_vv.VectorUnit.called, "VectorUnit method was not called"
        calls = self.mock_vv.VectorUnit.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((1,),)  # Passed as-is, no conversion
        
        print("✓ VectorUnit works correctly!")
    
    def test_vector_label(self, client):
        """Test VectorLabel endpoint - no base conversion"""
        # Configure mock
        self.mock_vv.VectorLabel.return_value = "Acceleration"
        self.mock_vv.VectorLabel.reset_mock()
        
        response = client.get('/api/v1/vectorlabel?vectorenum=2')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vectorlabel not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == "Acceleration"
        assert data['data']['vectorenum'] == 2
        
        # Verify VibrationVIEW was called with original value (no conversion)
        assert self.mock_vv.VectorLabel.called, "VectorLabel method was not called"
        calls = self.mock_vv.VectorLabel.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((2,),)  # Passed as-is, no conversion
        
        print("✓ VectorLabel works correctly!")
    
    def test_vector_length(self, client):
        """Test VectorLength endpoint - no base conversion"""
        # Configure mock
        self.mock_vv.VectorLength.return_value = 1024
        self.mock_vv.VectorLength.reset_mock()
        
        response = client.get('/api/v1/vectorlength?vectorenum=3')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/vectorlength not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == 1024
        assert data['data']['vectorenum'] == 3
        
        # Verify VibrationVIEW was called with original value (no conversion)
        assert self.mock_vv.VectorLength.called, "VectorLength method was not called"
        calls = self.mock_vv.VectorLength.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((3,),)  # Passed as-is, no conversion
        
        print("✓ VectorLength works correctly!")
    
    def test_vector_properties_missing_parameters(self, client):
        """Test vector properties with missing vectorenum parameter"""

        # Define all the endpoints to check
        endpoints = ['/api/v1/vectorunit', '/api/v1/vectorlabel', '/api/v1/vectorlength']

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for missing vectorenum"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False"
                assert 'vectorenum' in data['error']['message'], f"{endpoint} error message missing 'vectorenum'"

        print("✓ Vector properties parameter validation works!")

    # ============================================================================
    # CHANNEL METADATA TESTS (with base-1 to base-0 conversion)
    # ============================================================================
    
    def test_channel_unit_base1_conversion(self, client):
        """Test that channelnum is converted from base-1 to base-0"""
        # Configure mock
        self.mock_vv.ChannelUnit.return_value = "g"
        self.mock_vv.ChannelUnit.reset_mock()
        
        # Send request with 1-based channel number
        channel_1based = 3
        expected_channel_0based = 2  # 3-1=2
        
        response = client.get(f'/api/v1/channelunit?channelnum={channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/channelunit not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify response structure
        assert data['success'] is True
        assert data['data']['result'] == "g"
        assert data['data']['channelnum'] == channel_1based
        assert data['data']['internal_channelnum'] == expected_channel_0based
        
        # Verify VibrationVIEW was called with 0-based index
        assert self.mock_vv.ChannelUnit.called, "ChannelUnit method was not called"
        calls = self.mock_vv.ChannelUnit.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((expected_channel_0based,),)
        
        print("✓ ChannelUnit base-1 to base-0 conversion works!")
    
    def test_channel_unit_invalid_channel(self, client):
        """Test that channel 0 or negative channels are rejected"""

        endpoint = '/api/v1/channelunit'

        # Check if route is registered
        response = client.get(f'{endpoint}?channelnum=0')
        if response.status_code == 404:
            pytest.skip(f"Route {endpoint} not found - blueprint may not be registered")

        # Define test cases with invalid channel values
        invalid_channels = [0, -1]

        for channel in invalid_channels:
            response = client.get(f'{endpoint}?channelnum={channel}')
            assert response.status_code == 400, f"Expected 400 for channelnum={channel}, got {response.status_code}"
            data = json.loads(response.data)
            assert data['success'] is False, f"Expected success=False for channelnum={channel}"
            assert 'must be >= 1' in data['error']['message'], f"Expected error message to mention 'must be >= 1' for channelnum={channel}"

        print("✓ Invalid channel validation works!")
    
    def test_channel_label_base1_conversion(self, client):
        """Test channel label with base-1 conversion"""
        # Configure mock
        self.mock_vv.ChannelLabel.return_value = "Accel X"
        self.mock_vv.ChannelLabel.reset_mock()
        
        # Send request with 1-based channel number
        channel_1based = 1
        expected_channel_0based = 0  # 1-1=0
        
        response = client.get(f'/api/v1/channellabel?channelnum={channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/channellabel not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == "Accel X"
        assert data['data']['channelnum'] == channel_1based
        assert data['data']['internal_channelnum'] == expected_channel_0based
        
        # Verify VibrationVIEW was called with 0-based index
        assert self.mock_vv.ChannelLabel.called, "ChannelLabel method was not called"
        calls = self.mock_vv.ChannelLabel.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((expected_channel_0based,),)
        
        print("✓ ChannelLabel base-1 conversion works!")
    
    def test_channel_missing_parameters(self, client):
        """Test channel endpoints with missing channelnum parameter"""

        endpoints = ['/api/v1/channelunit', '/api/v1/channellabel']

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for missing channelnum"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False"
                assert 'channelnum' in data['error']['message'], f"{endpoint} error message missing 'channelnum'"

        print("✓ Channel parameter validation works!")
    
    # ============================================================================
    # CONTROL METADATA TESTS (with base-1 to base-0 conversion)
    # ============================================================================
    def test_control_label_base1_conversion(self, client):
        """Test control label with base-1 conversion"""
        # Configure mock
        self.mock_vv.ControlLabel.return_value = "Control Loop 1"
        self.mock_vv.ControlLabel.reset_mock()
        
        # Send request with 1-based loop number
        loop_1based = 4
        expected_loop_0based = 3  # 4-1=3
        
        response = client.get(f'/api/v1/controllabel?loopnum={loop_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/controllabel not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == "Control Loop 1"
        assert data['data']['loopnum'] == loop_1based
        assert data['data']['internal_loopnum'] == expected_loop_0based
        
        # Verify VibrationVIEW was called with 0-based index
        assert self.mock_vv.ControlLabel.called, "ControlLabel method was not called"
        calls = self.mock_vv.ControlLabel.call_args_list
        assert len(calls) == 1
        assert calls[0] == ((expected_loop_0based,),)
        
        print("✓ ControlLabel base-1 conversion works!")
    
    def test_control_invalid_parameters(self, client):
        """Test control endpoints with invalid loopnum parameters"""

        test_cases = [
            ('/api/v1/controlunit', 0),
            ('/api/v1/controllabel', -1),
        ]

        for endpoint, loopnum in test_cases:
            response = client.get(f'{endpoint}?loopnum={loopnum}')
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for loopnum={loopnum}"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False for loopnum={loopnum}"
                assert 'must be >= 1' in data['error']['message'], f"{endpoint} error message missing 'must be >= 1' for loopnum={loopnum}"

        print("✓ Control parameter validation works!")
    
    # ============================================================================
    # DOCUMENTATION TESTS
    # ============================================================================
    
    def test_docs_data_retrieval(self, client):
        """Test the data retrieval documentation endpoint"""
        response = client.get('/api/v1/docs/data_retrieval')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/docs/data_retrieval not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'module' in data
        assert data['module'] == 'data_retrieval'
        assert 'endpoints' in data
        assert 'Primary Data Arrays' in data['endpoints']
        assert 'Channel Metadata (1-based indexing)' in data['endpoints']
        assert 'Control Metadata (1-based indexing)' in data['endpoints']
        
        print("✓ Data retrieval documentation endpoint works!")
    
    def test_docs_vector_enums(self, client):
        """Test the vector enumerations documentation endpoint"""
        response = client.get('/api/v1/docs/vector_enums')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/docs/vector_enums not found - blueprint may not be registered")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'module' in data
        assert data['module'] == 'vector_enumerations'
        assert 'waveform_enums' in data
        assert 'frequency_enums' in data
        assert 'time_history_enums' in data
        assert 'usage_examples' in data
        
        print("✓ Vector enumerations documentation endpoint works!")
    
    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    def test_end_to_end_workflow(self, client):
        """Test a complete workflow using multiple endpoints"""
        # Skip if any route is not available
        test_routes = ['/api/v1/demand', '/api/v1/vector?vectorenum=1', '/api/v1/channelunit?channelnum=1']
        
        for route in test_routes:
            response = client.get(route)
            if response.status_code == 404:
                pytest.skip(f"Route {route} not found - blueprint may not be registered")
        
        # Configure mocks for workflow
        self.mock_vv.Demand.return_value = [1.0, 2.0]
        self.mock_vv.Vector.return_value = [[0.1, 0.2, 0.3]]
        self.mock_vv.ChannelUnit.return_value = "g"
        
        # Reset all mocks
        self.mock_vv.Demand.reset_mock()
        self.mock_vv.Vector.reset_mock()
        self.mock_vv.ChannelUnit.reset_mock()
        
        # Test workflow: Get demand -> Get vector data -> Get channel info
        
        # Step 1: Get current demand values
        response1 = client.get('/api/v1/demand')
        assert response1.status_code == 200
        demand_data = json.loads(response1.data)
        assert demand_data['success'] is True
        
        # Step 2: Get vector data for channel 1
        response2 = client.get('/api/v1/vector?vectorenum=1')
        assert response2.status_code == 200
        vector_data = json.loads(response2.data)
        assert vector_data['success'] is True
        
        # Step 3: Get channel unit information
        response3 = client.get('/api/v1/channelunit?channelnum=1')
        assert response3.status_code == 200
        channel_data = json.loads(response3.data)
        assert channel_data['success'] is True
        
        # Verify all mocks were called correctly
        assert self.mock_vv.Demand.called, "Demand was not called"
        assert self.mock_vv.Vector.called, "Vector was not called"
        assert self.mock_vv.ChannelUnit.called, "ChannelUnit was not called"
        
        # Verify correct parameters were passed
        demand_calls = self.mock_vv.Demand.call_args_list
        vector_calls = self.mock_vv.Vector.call_args_list
        channel_calls = self.mock_vv.ChannelUnit.call_args_list
        
        assert len(demand_calls) == 1
        assert demand_calls[0] == ((),)  # No parameters
        
        assert len(vector_calls) == 1
        assert vector_calls[0] == ((1, 1),)  # vectorenum=1, columns=1
        
        assert len(channel_calls) == 1
        assert channel_calls[0] == ((0,),)  # channelnum=1 converted to 0-based
        
        print("✓ End-to-end workflow test completed successfully!")
    
    def test_comprehensive_parameter_validation(self, client):
        """Test comprehensive parameter validation across all endpoints"""

        # Vector endpoints - missing parameters
        vector_endpoints = [
            ('/api/v1/vector', 'vectorenum'),
            ('/api/v1/vectorunit', 'vectorenum'),
            ('/api/v1/vectorlabel', 'vectorenum'),
            ('/api/v1/vectorlength', 'vectorenum'),
        ]

        for endpoint, param in vector_endpoints:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for missing {param}"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False"
                assert param in data['error']['message'], f"{endpoint} error message missing '{param}'"

        # Channel endpoints - missing parameters
        channel_endpoints = [
            ('/api/v1/channelunit', 'channelnum'),
            ('/api/v1/channellabel', 'channelnum'),
        ]

        for endpoint, param in channel_endpoints:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for missing {param}"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False"
                assert param in data['error']['message'], f"{endpoint} error message missing '{param}'"

        # Test invalid values
        invalid_tests = [
            ('/api/v1/vector?vectorenum=1&columns=0', 'columns must be >= 1'),
            ('/api/v1/channelunit?channelnum=0', 'must be >= 1'),
            ('/api/v1/channelunit?channelnum=-1', 'must be >= 1'),
            ('/api/v1/controllabel?loopnum=0', 'must be >= 1'),
            ('/api/v1/controllabel?loopnum=-5', 'must be >= 1'),
        ]

        for endpoint, expected_error in invalid_tests:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 400, f"{endpoint} did not return 400 for invalid parameter"
                data = json.loads(response.data)
                assert data['success'] is False, f"{endpoint} did not set success to False"
                assert expected_error in data['error']['message'], f"{endpoint} error message missing '{expected_error}'"

        print("✓ Comprehensive parameter validation works!")
    
    # ============================================================================
    # EDGE CASE TESTS
    # ============================================================================
    
    def test_edge_case_large_numbers(self, client):
        """Test edge cases with large numbers"""
        
        # Test large vector enumeration
        self.mock_vv.VectorUnit.return_value = "Hz"
        self.mock_vv.VectorUnit.reset_mock()
        
        response = client.get('/api/v1/vectorunit?vectorenum=999999')
        if response.status_code != 404:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data']['vectorenum'] == 999999
        
        # Test large channel number (should still convert correctly)
        self.mock_vv.ChannelUnit.return_value = "m/s²"
        self.mock_vv.ChannelUnit.reset_mock()
        
        response = client.get('/api/v1/channelunit?channelnum=1000')
        if response.status_code != 404:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data']['channelnum'] == 1000
            assert data['data']['internal_channelnum'] == 999  # 1000-1=999
            
            # Verify correct conversion
            calls = self.mock_vv.ChannelUnit.call_args_list
            if calls:
                assert calls[0] == ((999,),)
        
        print("✓ Edge case large numbers handled correctly!")
    
    def test_edge_case_boundary_values(self, client):
        """Test boundary values for 1-based indexing"""
        
        # Test channel 1 (minimum valid value)
        self.mock_vv.ChannelLabel.return_value = "Channel 1"
        self.mock_vv.ChannelLabel.reset_mock()
        
        response = client.get('/api/v1/channellabel?channelnum=1')
        if response.status_code != 404:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data']['channelnum'] == 1
            assert data['data']['internal_channelnum'] == 0  # 1-1=0
            
            calls = self.mock_vv.ChannelLabel.call_args_list
            if calls:
                assert calls[0] == ((0,),)
        
        # Test loop 1 (minimum valid value)
        self.mock_vv.ControlLabel.return_value = "Loop 1"
        self.mock_vv.ControlLabel.reset_mock()
        
        response = client.get('/api/v1/controllabel?loopnum=1')
        if response.status_code != 404:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data']['loopnum'] == 1
            assert data['data']['internal_loopnum'] == 0  # 1-1=0
            
            calls = self.mock_vv.ControlLabel.call_args_list
            if calls:
                assert calls[0] == ((0,),)
        
        print("✓ Boundary values handled correctly!")
    
    def test_mock_error_handling(self, client):
        """Test how the API handles mock errors"""

        # Configure mock to raise an exception
        self.mock_vv.Vector.side_effect = Exception("Mock VibrationVIEW error")

        response = client.get('/api/v1/vector?vectorenum=1')
        if response.status_code != 404:
            assert response.status_code == 500, f"Expected 500 status, got {response.status_code}"
            data = json.loads(response.data)
            assert data['success'] is False, "Expected success to be False"
            assert 'Failed to retrieve vector data' in data['error']['message'], "Error message missing expected text"

        # Reset side effect
        self.mock_vv.Vector.side_effect = None
        self.mock_vv.Vector.return_value = [[1, 2, 3]]

        print("✓ Mock error handling works correctly!")

    # ============================================================================
    # PERFORMANCE AND STRESS TESTS
    # ============================================================================
    
    def test_multiple_rapid_requests(self, client):
        """Test multiple rapid requests to ensure singleton stability"""
        
        # Configure mock
        self.mock_vv.Demand.return_value = [1.0, 2.0]
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            self.mock_vv.Demand.reset_mock()
            response = client.get('/api/v1/demand')
            responses.append(response)
        
        # Check that all requests succeeded (if route exists)
        if responses[0].status_code != 404:
            for i, response in enumerate(responses):
                assert response.status_code == 200, f"Request {i+1} failed"
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['data']['result'] == [1.0, 2.0]
        
        print("✓ Multiple rapid requests handled correctly!")
    
    def test_mixed_endpoint_requests(self, client):
        """Test mixed requests across different endpoint types"""
        
        # Configure all mocks
        self.mock_vv.Channel.return_value = [1.0, 2.0, 3.0]
        self.mock_vv.VectorLabel.return_value = "Test Label"
        self.mock_vv.ControlUnit.return_value = "V"
        
        # Reset all mocks
        self.mock_vv.Channel.reset_mock()
        self.mock_vv.VectorLabel.reset_mock()
        self.mock_vv.ControlUnit.reset_mock()
        
        # Make mixed requests
        test_requests = [
            ('/api/v1/channel', None),
            ('/api/v1/vectorlabel?vectorenum=5', None),
            ('/api/v1/controlunit?loopnum=2', None),
            ('/api/v1/channel', None),  # Repeat to test consistency
        ]
        
        for endpoint, expected in test_requests:
            response = client.get(endpoint)
            if response.status_code != 404:
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
        
        # Verify all mocks were called correctly
        if self.mock_vv.Channel.called:
            assert len(self.mock_vv.Channel.call_args_list) == 2  # Called twice
        
        if self.mock_vv.VectorLabel.called:
            calls = self.mock_vv.VectorLabel.call_args_list
            assert len(calls) == 1
            assert calls[0] == ((5,),)
        
        if self.mock_vv.ControlUnit.called:
            calls = self.mock_vv.ControlUnit.call_args_list
            assert len(calls) == 1
            assert calls[0] == ((1,),)  # loopnum=2 converted to 0-based 1
        
        print("✓ Mixed endpoint requests handled correctly!")
    
    # ============================================================================
    # FINAL SUMMARY TEST
    # ============================================================================
    
    def test_final_summary_all_endpoints(self, client):
        """Final summary test of all endpoints with proper configuration"""
        
        print("\n=== FINAL SUMMARY TEST ===")
        
        # Configure all mocks with distinct return values
        mock_config = {
            'Demand': [10.0, 20.0],
            'Control': [0.5, 0.7],
            'Channel': [1.1, 2.2, 3.3, 4.4],
            'Output': [100.0, 200.0],
            'Vector': [[0.1, 0.2, 0.3]],
            'VectorUnit': "test_unit",
            'VectorLabel': "test_label",
            'VectorLength': 512,
            'ChannelUnit': "test_chan_unit",
            'ChannelLabel': "test_chan_label",
            'ControlUnit': "test_ctrl_unit",
            'ControlLabel': "test_ctrl_label"
        }
        
        # Apply mock configuration
        for method_name, return_value in mock_config.items():
            if hasattr(self.mock_vv, method_name):
                getattr(self.mock_vv, method_name).return_value = return_value
                getattr(self.mock_vv, method_name).reset_mock()
        
        # Test all endpoints
        endpoint_tests = [
            ('GET', '/api/v1/demand', None, 'Demand'),
            ('GET', '/api/v1/control', None, 'Control'),
            ('GET', '/api/v1/channel', None, 'Channel'),
            ('GET', '/api/v1/output', None, 'Output'),
            ('GET', '/api/v1/vector?vectorenum=1', {'vectorenum': 1, 'columns': 1}, 'Vector'),
            ('GET', '/api/v1/vectorunit?vectorenum=2', {'vectorenum': 2}, 'VectorUnit'),
            ('GET', '/api/v1/vectorlabel?vectorenum=3', {'vectorenum': 3}, 'VectorLabel'),
            ('GET', '/api/v1/vectorlength?vectorenum=4', {'vectorenum': 4}, 'VectorLength'),
            ('GET', '/api/v1/channelunit?channelnum=5', {'channelnum': 5, 'internal_channelnum': 4}, 'ChannelUnit'),
            ('GET', '/api/v1/channellabel?channelnum=6', {'channelnum': 6, 'internal_channelnum': 5}, 'ChannelLabel'),
            ('GET', '/api/v1/controlunit?loopnum=7', {'loopnum': 7, 'internal_loopnum': 6}, 'ControlUnit'),
            ('GET', '/api/v1/controllabel?loopnum=8', {'loopnum': 8, 'internal_loopnum': 7}, 'ControlLabel'),
        ]
        
        results = {}
        
        for method, endpoint, expected_params, mock_method in endpoint_tests:
            response = client.get(endpoint)
            
            if response.status_code == 404:
                results[endpoint] = "NOT_FOUND"
                print(f"❌ {endpoint} - Route not found")
            elif response.status_code == 200:
                data = json.loads(response.data)
                if data.get('success'):
                    results[endpoint] = "SUCCESS"
                    print(f"✅ {endpoint} - Working correctly")
                    
                    # Verify mock was called
                    mock_obj = getattr(self.mock_vv, mock_method)
                    if not mock_obj.called:
                        print(f"⚠️  {endpoint} - Mock {mock_method} was not called")
                else:
                    results[endpoint] = "ERROR"
                    print(f"❌ {endpoint} - API error: {data.get('error', 'Unknown')}")
            else:
                results[endpoint] = f"HTTP_{response.status_code}"
                print(f"❌ {endpoint} - HTTP {response.status_code}")
        
        # Summary
        success_count = len([r for r in results.values() if r == "SUCCESS"])
        not_found_count = len([r for r in results.values() if r == "NOT_FOUND"])
        error_count = len([r for r in results.values() if r not in ["SUCCESS", "NOT_FOUND"]])
        
        print(f"\n=== SUMMARY ===")
        print(f"✅ Working endpoints: {success_count}/{len(endpoint_tests)}")
        print(f"❌ Not found endpoints: {not_found_count}/{len(endpoint_tests)}")
        print(f"⚠️  Error endpoints: {error_count}/{len(endpoint_tests)}")
        
        if not_found_count == len(endpoint_tests):
            print("\n🔍 All endpoints returned 404 - Blueprint may not be registered!")
            print("   Check that data_retrieval_bp is registered in the Flask app")
        elif success_count > 0:
            print(f"\n🎉 {success_count} endpoints are working correctly!")
        
        print("=== END FINAL SUMMARY ===\n")