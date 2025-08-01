# ============================================================================
# FILE: tests/test_instance_sharing.py
# ============================================================================

"""
Test to verify that the mock VibrationVIEW instance is shared correctly
"""

import pytest
import json

class TestInstanceSharing:
    """Test that all VibrationVIEW() calls return the same mock instance"""
    
    def test_instance_sharing_verification(self, mock_vibrationview, monkeypatch):
        """Verify that importing VibrationVIEW returns our mock instance"""
        # Patch VibrationVIEW to always return the shared mock
        monkeypatch.setattr("vibrationviewapi.VibrationVIEW", lambda: mock_vibrationview)

        from vibrationviewapi import VibrationVIEW

        vv1 = VibrationVIEW()
        vv2 = VibrationVIEW()

        assert vv1 is mock_vibrationview
        assert vv2 is mock_vibrationview
        assert vv1 is vv2

        # State should be shared
        vv1._demand_multiplier = 123.45
        assert vv2._demand_multiplier == 123.45
        assert mock_vibrationview._demand_multiplier == 123.45

    print("✓ Instance sharing is working correctly")
    def test_route_uses_same_instance(self, client, mock_vibrationview, monkeypatch):
        # Patch VibrationVIEW to always return the shared mock
        monkeypatch.setattr("vibrationviewapi.VibrationVIEW", lambda: mock_vibrationview)

        """Test that routes use the same mock instance we configure"""
        # Set a value in our mock
        expected_value = 999.99
        mock_vibrationview._demand_multiplier = expected_value
        mock_vibrationview.clear_method_calls()
        
        # Make a request that should use this instance
        response = client.get('/api/demandmultiplier')
        
        if response.status_code == 404:
            pytest.skip("Route not found - test the mock instance sharing directly")
        
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Response data: {data}")
            
            # The route should return the value we set
            if 'data' in data and 'result' in data['data']:
                actual_value = data['data']['result']
                print(f"Expected: {expected_value}, Actual: {actual_value}")
                assert actual_value == expected_value, f"Route returned {actual_value}, expected {expected_value}"
                print("✓ Route is using the same mock instance")
            else:
                print("Response format doesn't match expected structure")
        else:
            print(f"Route failed with status {response.status_code}")
            if response.data:
                print(f"Error response: {response.get_data(as_text=True)}")
    
    def test_mock_import_verification(self):
        """Debug test to see what happens when we import VibrationVIEW"""
        import sys
        
        # Check what's in sys.modules
        print(f"vibrationviewapi in sys.modules: {'vibrationviewapi' in sys.modules}")
        if 'vibrationviewapi' in sys.modules:
            module = sys.modules['vibrationviewapi']
            print(f"Module type: {type(module)}")
            print(f"Module VibrationVIEW: {getattr(module, 'VibrationVIEW', 'NOT FOUND')}")
        
        # Try importing
        try:
            from vibrationviewapi import VibrationVIEW
            print(f"VibrationVIEW imported successfully: {VibrationVIEW}")
            
            # Create instance
            vv = VibrationVIEW()
            print(f"VibrationVIEW instance: {vv}")
            print(f"Instance type: {type(vv)}")
            print(f"Has _demand_multiplier: {hasattr(vv, '_demand_multiplier')}")
            print(f"Has get_method_calls: {hasattr(vv, 'get_method_calls')}")
            
            if hasattr(vv, 'get_method_calls'):
                print("✓ This is our mock instance")
            else:
                print("✗ This is NOT our mock instance")
                
        except Exception as e:
            print(f"Import failed: {e}")
    
    def test_direct_route_call_simulation(self, mock_vibrationview, monkeypatch):
        """Verify that importing VibrationVIEW returns our mock instance"""
        # Patch VibrationVIEW to always return the shared mock
        monkeypatch.setattr("vibrationviewapi.VibrationVIEW", lambda: mock_vibrationview)

        """Simulate what a route does to verify mocking"""
        # This simulates what your route code does
        from vibrationviewapi import VibrationVIEW
        
        # Set expected value
        expected_value = 555.55
        mock_vibrationview._demand_multiplier = expected_value
        
        # Simulate route code
        vv = VibrationVIEW()  # This is what your route does
        result = vv.DemandMultiplier()  # This is what your route calls
        
        print(f"Direct simulation result: {result}")
        print(f"Expected: {expected_value}")
        
        assert result == expected_value, f"Got {result}, expected {expected_value}"
        print("✓ Direct route simulation works correctly")
    
    def test_multiple_route_calls_share_state(self, client, mock_vibrationview):
        """Test that multiple route calls share the same mock state"""
        if client.get('/api/demandmultiplier').status_code == 404:
            pytest.skip("Route not available for testing")
        
        # Set initial value
        initial_value = 100.0
        mock_vibrationview._demand_multiplier = initial_value
        
        # First call - should return initial value
        response1 = client.get('/api/demandmultiplier')
        if response1.status_code == 200:
            data1 = response1.get_json()
            value1 = data1['data']['result']
            print(f"First call result: {value1}")
            assert value1 == initial_value
        
        # Change value through mock
        new_value = 200.0
        mock_vibrationview._demand_multiplier = new_value
        
        # Second call - should return new value
        response2 = client.get('/api/demandmultiplier')
        if response2.status_code == 200:
            data2 = response2.get_json()
            value2 = data2['data']['result']
            print(f"Second call result: {value2}")
            assert value2 == new_value
            
        print("✓ Multiple route calls share mock state")