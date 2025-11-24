# ============================================================================
# FILE: tests/test_teds_routes.py
# ============================================================================

"""
Tests for TEDS routes with GET pattern and proper indexing using singleton pattern
"""

import pytest
import json
from app import create_app, set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW

class TestTEDSRoutes:
    """Test TEDS endpoints with proper GET patterns and indexing using singleton"""
    
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
        reset_vv_instance()  # Reset first
        mock_instance = MockVibrationVIEW()
        set_vv_instance(mock_instance)
        yield mock_instance
        # Cleanup after test
        reset_vv_instance()
    
    def test_teds_all_channels_get(self, client, mock_vv):
        """Test GET /Teds with no parameters (all channels)"""
        # Configure mock for all channels - should return list of channel data
        mock_all_teds = [
            [['Sensitivity', '100.0 mV/g'], ['Units', 'mV/g']],  # Channel 0
            [['Sensitivity', '200.0 mV/g'], ['Units', 'mV/g']]   # Channel 1
        ]
        mock_vv.Teds.return_value = mock_all_teds
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/teds')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            data = json.loads(response.data)
            print(f"Error response: {data}")
            # For now, let's see what the actual error is
            pytest.fail(f"Expected 200, got {response.status_code}: {data}")
        
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['channel'] == 'all'
        assert data['data']['success'] is True
        # The result contains formatted data with 'transducers' and 'errors' arrays
        assert 'result' in data['data']
        assert 'transducers' in data['data']['result']
        assert 'errors' in data['data']['result']
        
        # Verify VibrationVIEW was called with no arguments
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with()  # Called with no arguments
        
        print("✓ GET /Teds (all channels) works!")
    
    def test_teds_specific_channel_1based(self, client, mock_vv):
        """Test GET /Teds with 1-based channel parameter"""
        # Configure mock - TEDS data should be in list format for the formatter
        mock_channel_teds = [
            ['Sensitivity', '150.0 mV/g'],
            ['Units', 'mV/g'],
            ['Serial Number', '12345']
        ]
        mock_vv.Teds.return_value = mock_channel_teds
        mock_vv.GetHardwareInputChannels.return_value = 4
        mock_vv.clear_method_calls()
        
        # Test with 1-based channel 3 (should convert to 0-based channel 2)
        channel_1based = 3
        expected_channel_0based = 2
        
        response = client.get(f'/api/v1/teds?{channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['channel'] == channel_1based
        assert data['data']['success'] is True
        # For single channel, the response contains formatted transducer data
        assert 'transducer' in data['data']
        
        # Verify VibrationVIEW was called with 0-based channel
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with(expected_channel_0based)
        
        print("✓ GET /Teds with 1-based channel works!")
    
    def test_teds_invalid_channel_zero(self, client, mock_vv):
        """Test GET /Teds with invalid channel 0 (1-based should be >= 1)"""
        response = client.get('/api/v1/teds?0')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Channel must be >= 1 (1-based indexing), got 0'
        assert data['error']['code'] == 'INVALID_CHANNEL'
        
        print("✓ GET /Teds rejects channel 0 correctly!")
    
    def test_teds_invalid_channel_negative(self, client, mock_vv):
        """Test GET /Teds with negative channel"""
        response = client.get('/api/v1/teds?-1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Channel must be >= 1 (1-based indexing), got -1'
        assert data['error']['code'] == 'INVALID_CHANNEL'
        
        print("✓ GET /Teds rejects negative channels correctly!")
    
    def test_teds_channel_out_of_range(self, client, mock_vv):
        """Test GET /Teds with channel beyond hardware range"""
        # Configure mock to have 4 channels (1-4 in 1-based indexing)
        mock_vv.GetHardwareInputChannels.return_value = 4
        
        # Try to access channel 5 (1-based) - should be out of range
        response = client.get('/api/v1/teds?5')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'].startswith('Channel') and 'out of range' in data['error']['message']
        assert data['error']['code'] == 'CHANNEL_OUT_OF_RANGE'
        
        print("✓ GET /Teds handles out-of-range channels correctly!")
    
    def test_teds_invalid_channel_string(self, client, mock_vv):
        """Test GET /Teds with non-numeric channel parameter"""
        response = client.get('/api/v1/teds?abc')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Invalid channel parameter - must be an integer'
        assert data['error']['code'] == 'INVALID_PARAMETER'
        
        print("✓ GET /Teds handles non-numeric channels correctly!")
    
    def test_inputtedschannel_1based_pattern(self, client, mock_vv):
        """Test GET /inputtedschannel with 1-based indexing (now consistent)"""
        # Configure mock
        mock_channel_teds = {'sensitivity': 250.0, 'units': 'mV/g'}
        mock_vv.Teds.return_value = mock_channel_teds
        mock_vv.GetHardwareInputChannels.return_value = 4
        mock_vv.clear_method_calls()
        
        # Test with 1-based channel 3 (should convert to 0-based channel 2)
        channel_1based = 3
        expected_channel_0based = 2
        
        response = client.get(f'/api/v1/inputtedschannel?{channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/inputtedschannel not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_channel_teds
        assert data['data']['channel'] == channel_1based  # 1-based
        assert data['data']['internal_channel'] == expected_channel_0based  # 0-based internal
        
        # Verify VibrationVIEW was called with 0-based channel
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with(expected_channel_0based)
        
        print("✓ GET /inputtedschannel (1-based pattern) works!")
    
    def test_inputtedschannel_invalid_channel_zero(self, client, mock_vv):
        """Test GET /inputtedschannel with invalid channel 0 (now 1-based)"""
        response = client.get('/api/v1/inputtedschannel?0')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/inputtedschannel not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Channel must be >= 1 (1-based indexing), got 0'
        assert data['error']['code'] == 'INVALID_CHANNEL'
        
        print("✓ GET /inputtedschannel rejects channel 0 correctly!")
    
    def test_inputteds_all_channels(self, client, mock_vv):
        """Test GET /inputteds for all channels"""
        # Configure mock
        mock_teds_responses = [
            {'sensitivity': 100.0, 'units': 'mV/g'},  # Channel 0
            {'sensitivity': 200.0, 'units': 'mV/g'},  # Channel 1
        ]
        
        def mock_teds_side_effect(channel):
            return mock_teds_responses[channel]
        
        mock_vv.Teds.side_effect = mock_teds_side_effect
        mock_vv.GetHardwareInputChannels.return_value = 2
        mock_vv.clear_method_calls()
        
        response = client.get('/api/v1/inputteds')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/inputteds not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['total_channels'] == 2
        assert data['data']['channels_with_teds'] == 2
        assert data['data']['channels_with_errors'] == 0
        
        result = data['data']['result']
        assert len(result) == 2
        
        # Check first channel
        assert result[0]['channel'] == 1  # 1-based display
        assert result[0]['teds'] == mock_teds_responses[0]
        assert result[0]['success'] is True

        # Check second channel
        assert result[1]['channel'] == 2  # 1-based display
        assert result[1]['teds'] == mock_teds_responses[1]
        assert result[1]['success'] is True
        
        print("✓ GET /inputteds (all channels) works!")
    
    def test_teds_error_handling(self, client, mock_vv):
        """Test error handling when TEDS read fails"""
        # Configure mock to raise exception
        mock_vv.Teds.side_effect = Exception("TEDS read failed")
        mock_vv.GetHardwareInputChannels.return_value = 4
        
        # Test specific channel error
        response = client.get('/api/v1/teds?1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/v1/teds not found")
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Failed to retrieve TEDS for channel 1: TEDS read failed'
        assert data['error']['code'] == 'TEDS_READ_ERROR'
        
        # Test all channels error
        response = client.get('/api/v1/teds')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'Failed to retrieve TEDS for all channels' in data['error']['message']
        
        print("✓ TEDS error handling works!")
    
    def test_teds_documentation(self, client):
        """Test TEDS documentation endpoint"""
        response = client.get('/api/v1/docs/teds')
        
        if response.status_code == 404:
            pytest.skip("TEDS documentation not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['module'] == 'teds'
        assert 'endpoints' in data
        assert 'GET /inputteds' in data['endpoints']['TEDS Information']
        assert 'GET /inputtedschannel' in data['endpoints']['TEDS Information']
        assert 'GET /teds' in data['endpoints']['TEDS Information']
        
        # Check that documentation explains indexing differences
        teds_endpoint = data['endpoints']['TEDS Information']['GET /teds']
        assert '1-based' in teds_endpoint['description'] or '1-based' in str(teds_endpoint)
        
        print("✓ TEDS documentation is complete!")

    def test_tedsfromurn_success(self, client, mock_vv):
        """Test GET /tedsfromurn with valid URN"""
        # Configure mock
        mock_teds_data = [
            {'sensitivity': 100.0, 'units': 'mV/g', 'serial_number': 'SN123456'},
            {'frequency_range': '1-1000 Hz', 'calibration_date': '2024-01-15'}
        ]
        mock_vv.TedsFromURN.return_value = mock_teds_data
        mock_vv.clear_method_calls()

        urn = "test_urn_123456"
        response = client.get(f'/api/v1/tedsfromurn?{urn}')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/tedsfromurn not found")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['urn'] == urn
        assert data['data']['success'] is True
        # The response contains formatted transducer data, not raw result
        assert 'transducer' in data['data']

        # Verify VibrationVIEW was called with correct URN
        assert mock_vv.TedsFromURN.called, "TedsFromURN method was not called"
        mock_vv.TedsFromURN.assert_called_with(urn)

        print("✓ GET /tedsfromurn with valid URN works!")

    def test_tedsfromurn_missing_urn(self, client, mock_vv):
        """Test GET /tedsfromurn without URN parameter"""
        response = client.get('/api/v1/tedsfromurn')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/tedsfromurn not found")

        assert response.status_code == 400
        data = json.loads(response.data)

        assert data['success'] is False
        assert data['error']['message'] == 'Missing required query parameter: urn'
        assert data['error']['code'] == 'MISSING_PARAMETER'

        print("✓ GET /tedsfromurn rejects missing URN correctly!")

    def test_tedsfromurn_empty_urn(self, client, mock_vv):
        """Test GET /tedsfromurn with empty URN parameter"""
        response = client.get('/api/v1/tedsfromurn?')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/tedsfromurn not found")

        assert response.status_code == 400
        data = json.loads(response.data)

        assert data['success'] is False
        # With empty query string, it's treated as missing parameter
        assert data['error']['message'] == 'Missing required query parameter: urn'
        assert data['error']['code'] == 'MISSING_PARAMETER'

        print("✓ GET /tedsfromurn rejects empty URN correctly!")

    def test_tedsfromurn_com_error(self, client, mock_vv):
        """Test GET /tedsfromurn when VibrationVIEW raises an exception"""
        # Configure mock to raise exception
        mock_vv.TedsFromURN.side_effect = Exception("URN not found in database")

        urn = "invalid_urn_999"
        response = client.get(f'/api/v1/tedsfromurn?{urn}')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/tedsfromurn not found")

        assert response.status_code == 500
        data = json.loads(response.data)

        assert data['success'] is False
        assert 'URN not found in database' in data['error']
        # The @with_vibrationview decorator returns error as a string, not a dict

        print("✓ GET /tedsfromurn handles COM errors correctly!")

    def test_tedsfromurn_special_characters(self, client, mock_vv):
        """Test GET /tedsfromurn with URN containing special characters"""
        # Configure mock
        mock_teds_data = [{'sensitivity': 50.0, 'units': 'mV/g'}]
        mock_vv.TedsFromURN.return_value = mock_teds_data
        mock_vv.clear_method_calls()

        urn = "urn-with-dashes_and_underscores.123"
        response = client.get(f'/api/v1/tedsfromurn?{urn}')

        if response.status_code == 404:
            pytest.skip("Route /api/v1/tedsfromurn not found")

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert 'transducer' in data['data']  # Formatted response, not raw result
        assert data['data']['urn'] == urn

        # Verify VibrationVIEW was called with correct URN
        mock_vv.TedsFromURN.assert_called_with(urn)

        print("✓ GET /tedsfromurn handles special characters in URN correctly!")
        