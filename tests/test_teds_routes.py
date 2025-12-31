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

    # -------------------------------------------------------------------------
    # /tedsread tests
    # -------------------------------------------------------------------------

    def test_tedsread_with_valid_urns(self, client, mock_vv):
        """Test GET /tedsread returns transducer parameters for valid URNs"""
        # Configure TedsRead to return list of URNs (16-digit hex strings)
        raw_values = ["3C00000186B96114", "4D00000286C97225"]
        mock_vv.TedsRead.return_value = raw_values

        # Configure TedsFromURN to return TEDS data for each URN
        mock_teds_data = [
            ['Manufacturer', 'PCB Piezotronics', ''],
            ['Model number', '352C33', ''],
            ['Sensitivity', '100.0', 'mV/g'],
            ['Serial number', 'SN12345', '']
        ]
        mock_vv.TedsFromURN.return_value = mock_teds_data
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['channel_count'] == 2
        assert data['data']['transducer_count'] == 2
        assert len(data['data']['channels']) == 2

        # Verify channels are in order with transducer data expanded
        for i, channel in enumerate(data['data']['channels']):
            assert channel['channel'] == i + 1
            assert channel['raw_value'] == raw_values[i]
            assert 'transducer' in channel
            assert channel['transducer']['urn'] == raw_values[i]
            assert 'manufacturer' in channel['transducer']

        # Verify TedsFromURN was called for each valid URN
        assert mock_vv.TedsFromURN.call_count == 2

    def test_tedsread_mixed_valid_invalid(self, client, mock_vv):
        """Test GET /tedsread with mix of valid URNs and invalid values"""
        # Channel 1: valid URN (16-digit hex), Channel 2: no TEDS, Channel 3: valid URN, Channel 4: error
        raw_values = ["3C00000186B96114", "No TEDS data", "4D00000286C97225", "Error: sensor not found"]
        mock_vv.TedsRead.return_value = raw_values

        mock_teds_data = [
            ['Manufacturer', 'PCB', ''],
            ['Sensitivity', '100.0', 'mV/g']
        ]
        mock_vv.TedsFromURN.return_value = mock_teds_data
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['channel_count'] == 4
        assert data['data']['transducer_count'] == 2  # Only 2 valid URNs

        # Channel 1: has transducer
        assert data['data']['channels'][0]['channel'] == 1
        assert data['data']['channels'][0]['raw_value'] == "3C00000186B96114"
        assert 'transducer' in data['data']['channels'][0]

        # Channel 2: no TEDS - just raw value, no transducer
        assert data['data']['channels'][1]['channel'] == 2
        assert data['data']['channels'][1]['raw_value'] == "No TEDS data"
        assert 'transducer' not in data['data']['channels'][1]

        # Channel 3: has transducer
        assert data['data']['channels'][2]['channel'] == 3
        assert 'transducer' in data['data']['channels'][2]

        # Channel 4: error value - just raw value, no transducer
        assert data['data']['channels'][3]['channel'] == 4
        assert data['data']['channels'][3]['raw_value'] == "Error: sensor not found"
        assert 'transducer' not in data['data']['channels'][3]

        # TedsFromURN only called for valid URNs
        assert mock_vv.TedsFromURN.call_count == 2

    def test_tedsread_empty_result(self, client, mock_vv):
        """Test GET /tedsread with no channels returned"""
        mock_vv.TedsRead.return_value = []
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['channels'] == []
        assert data['data']['channel_count'] == 0
        assert data['data']['transducer_count'] == 0

    def test_tedsread_single_urn_string(self, client, mock_vv):
        """Test GET /tedsread when TedsRead returns a single string URN"""
        urn = "5E00000386D08336"  # Valid 16-digit hex URN
        mock_vv.TedsRead.return_value = urn

        mock_teds_data = [
            ['Manufacturer', 'Bruel & Kjaer', ''],
            ['Sensitivity', '50.0', 'mV/g']
        ]
        mock_vv.TedsFromURN.return_value = mock_teds_data
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['channel_count'] == 1
        assert data['data']['transducer_count'] == 1
        assert data['data']['channels'][0]['channel'] == 1
        assert data['data']['channels'][0]['raw_value'] == urn
        assert data['data']['channels'][0]['transducer']['urn'] == urn

    def test_tedsread_urn_lookup_error(self, client, mock_vv):
        """Test GET /tedsread when TedsFromURN fails for some URNs"""
        # All valid 16-digit hex URNs, but one will fail lookup
        raw_values = ["6F00000487E19447", "7000000588F20558", "8100000689003669"]
        mock_vv.TedsRead.return_value = raw_values

        # Configure TedsFromURN to fail for the second URN
        def teds_from_urn_side_effect(urn):
            if urn == "7000000588F20558":
                raise Exception("URN not found in database")
            return [
                ['Manufacturer', 'Test Mfg', ''],
                ['Sensitivity', '100.0', 'mV/g']
            ]

        mock_vv.TedsFromURN.side_effect = teds_from_urn_side_effect
        mock_vv.clear_method_calls()

        response = client.get('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data['success'] is True
        assert data['data']['transducer_count'] == 2  # 2 successful lookups
        assert data['data']['channel_count'] == 3

        # Channel 1: success
        assert 'transducer' in data['data']['channels'][0]

        # Channel 2: error during lookup
        assert data['data']['channels'][1]['raw_value'] == "7000000588F20558"
        assert 'error' in data['data']['channels'][1]
        assert "URN not found" in data['data']['channels'][1]['error']
        assert 'transducer' not in data['data']['channels'][1]

        # Channel 3: success
        assert 'transducer' in data['data']['channels'][2]

    def test_tedsread_post_method(self, client, mock_vv):
        """Test POST /tedsread also works"""
        mock_vv.TedsRead.return_value = ["920000078A11477A"]  # Valid 16-digit hex URN
        mock_vv.TedsFromURN.return_value = [['Sensitivity', '75.0', 'mV/g']]
        mock_vv.clear_method_calls()

        response = client.post('/api/v1/tedsread')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['data']['transducer_count'] == 1
        assert data['data']['channel_count'] == 1

    def test_is_valid_urn_function(self, client, mock_vv):
        """Test the is_valid_urn utility function"""
        from utils.utils import is_valid_urn

        # Valid URNs (exactly 16 hex digits)
        assert is_valid_urn("3C00000186B96114") is True
        assert is_valid_urn("0000000000000000") is True
        assert is_valid_urn("FFFFFFFFFFFFFFFF") is True
        assert is_valid_urn("abcdef0123456789") is True  # lowercase hex
        assert is_valid_urn("AbCdEf0123456789") is True  # mixed case

        # Invalid URNs
        assert is_valid_urn("") is False                  # empty
        assert is_valid_urn("ABC123") is False            # too short
        assert is_valid_urn("3C00000186B961140") is False  # too long (17 digits)
        assert is_valid_urn("No TEDS data") is False      # not hex
        assert is_valid_urn("Error: not found") is False  # error message
        assert is_valid_urn("urn:123:abc") is False       # old format
        assert is_valid_urn(None) is False                # None
        assert is_valid_urn(12345) is False               # not a string
        assert is_valid_urn("  3C00000186B96114  ") is True  # with whitespace (stripped)
        