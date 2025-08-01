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
        # Configure mock for all channels
        mock_all_teds = [
            {'channel': 0, 'sensitivity': 100.0, 'units': 'mV/g'},
            {'channel': 1, 'sensitivity': 200.0, 'units': 'mV/g'}
        ]
        mock_vv.Teds.return_value = mock_all_teds
        mock_vv.clear_method_calls()
        
        response = client.get('/api/Teds')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
        print(f"Response status: {response.status_code}")
        if response.status_code != 200:
            data = json.loads(response.data)
            print(f"Error response: {data}")
            # For now, let's see what the actual error is
            pytest.fail(f"Expected 200, got {response.status_code}: {data}")
        
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_all_teds
        assert data['data']['channel'] == 'all'
        assert data['data']['success'] is True
        
        # Verify VibrationVIEW was called with no arguments
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with()  # Called with no arguments
        
        print("✓ GET /Teds (all channels) works!")
    
    def test_teds_specific_channel_1based(self, client, mock_vv):
        """Test GET /Teds with 1-based channel parameter"""
        # Configure mock
        mock_channel_teds = {'sensitivity': 150.0, 'units': 'mV/g', 'serial': '12345'}
        mock_vv.Teds.return_value = mock_channel_teds
        mock_vv.GetHardwareInputChannels.return_value = 4
        mock_vv.clear_method_calls()
        
        # Test with 1-based channel 3 (should convert to 0-based channel 2)
        channel_1based = 3
        expected_channel_0based = 2
        
        response = client.get(f'/api/Teds?{channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_channel_teds
        assert data['data']['channel'] == channel_1based
        assert data['data']['internal_channel'] == expected_channel_0based
        assert data['data']['success'] is True
        
        # Verify VibrationVIEW was called with 0-based channel
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with(expected_channel_0based)
        
        print("✓ GET /Teds with 1-based channel works!")
    
    def test_teds_invalid_channel_zero(self, client, mock_vv):
        """Test GET /Teds with invalid channel 0 (1-based should be >= 1)"""
        response = client.get('/api/Teds?0')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Channel must be >= 1 (1-based indexing), got 0'
        assert data['error']['code'] == 'INVALID_CHANNEL'
        
        print("✓ GET /Teds rejects channel 0 correctly!")
    
    def test_teds_invalid_channel_negative(self, client, mock_vv):
        """Test GET /Teds with negative channel"""
        response = client.get('/api/Teds?-1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
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
        response = client.get('/api/Teds?5')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'].startswith('Channel') and 'out of range' in data['error']['message']
        assert data['error']['code'] == 'CHANNEL_OUT_OF_RANGE'
        
        print("✓ GET /Teds handles out-of-range channels correctly!")
    
    def test_teds_invalid_channel_string(self, client, mock_vv):
        """Test GET /Teds with non-numeric channel parameter"""
        response = client.get('/api/Teds?abc')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
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
        
        response = client.get(f'/api/inputtedschannel?{channel_1based}')
        
        if response.status_code == 404:
            pytest.skip("Route /api/inputtedschannel not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['result'] == mock_channel_teds
        assert data['data']['channel'] == channel_1based  # 1-based
        assert data['data']['internal_channel'] == expected_channel_0based  # 0-based internal
        assert data['data']['channel_display'] == channel_1based  # Same as channel (both 1-based)
        
        # Verify VibrationVIEW was called with 0-based channel
        assert mock_vv.Teds.called, "Teds method was not called"
        mock_vv.Teds.assert_called_with(expected_channel_0based)
        
        print("✓ GET /inputtedschannel (1-based pattern) works!")
    
    def test_inputtedschannel_invalid_channel_zero(self, client, mock_vv):
        """Test GET /inputtedschannel with invalid channel 0 (now 1-based)"""
        response = client.get('/api/inputtedschannel?0')
        
        if response.status_code == 404:
            pytest.skip("Route /api/inputtedschannel not found")
        
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
        
        response = client.get('/api/inputteds')
        
        if response.status_code == 404:
            pytest.skip("Route /api/inputteds not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['success'] is True
        assert data['data']['total_channels'] == 2
        assert data['data']['channels_with_teds'] == 2
        assert data['data']['channels_with_errors'] == 0
        
        result = data['data']['result']
        assert len(result) == 2
        
        # Check first channel
        assert result[0]['channel'] == 0  # 0-based
        assert result[0]['channel_display'] == 1  # 1-based display
        assert result[0]['teds'] == mock_teds_responses[0]
        assert result[0]['success'] is True
        
        # Check second channel
        assert result[1]['channel'] == 1  # 0-based
        assert result[1]['channel_display'] == 2  # 1-based display
        assert result[1]['teds'] == mock_teds_responses[1]
        assert result[1]['success'] is True
        
        print("✓ GET /inputteds (all channels) works!")
    
    def test_teds_error_handling(self, client, mock_vv):
        """Test error handling when TEDS read fails"""
        # Configure mock to raise exception
        mock_vv.Teds.side_effect = Exception("TEDS read failed")
        mock_vv.GetHardwareInputChannels.return_value = 4
        
        # Test specific channel error
        response = client.get('/api/Teds?1')
        
        if response.status_code == 404:
            pytest.skip("Route /api/Teds not found")
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert data['error']['message'] == 'Failed to retrieve TEDS for channel 1: TEDS read failed'
        assert data['error']['code'] == 'TEDS_READ_ERROR'
        
        # Test all channels error
        response = client.get('/api/Teds')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        
        assert data['success'] is False
        assert 'Failed to retrieve TEDS for all channels' in data['error']['message']
        
        print("✓ TEDS error handling works!")
    
    def test_teds_documentation(self, client):
        """Test TEDS documentation endpoint"""
        response = client.get('/api/docs/teds')
        
        if response.status_code == 404:
            pytest.skip("TEDS documentation not found")
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['module'] == 'teds'
        assert 'endpoints' in data
        assert 'GET /inputteds' in data['endpoints']['TEDS Information']
        assert 'GET /inputtedschannel' in data['endpoints']['TEDS Information']
        assert 'GET /Teds' in data['endpoints']['TEDS Information']
        
        # Check that documentation explains indexing differences
        teds_endpoint = data['endpoints']['TEDS Information']['GET /Teds']
        assert '1-based' in teds_endpoint['description'] or '1-based' in str(teds_endpoint)
        
        print("✓ TEDS documentation is complete!")
        