# ============================================================================
# FILE: tests/test_simple.py
# ============================================================================
import pytest
import json
from unittest.mock import patch
from app import create_app, set_vv_instance, reset_vv_instance
from tests.mocks.mock_vibrationviewapi import MockVibrationVIEW  # Add this line

class TestSimple:
    def test_debug_singleton_behavior(self, client):
        """Debug test to understand what's happening with the singleton"""
        from app import get_vv_instance, _vv_instance
        
        print(f"Initial singleton instance: {_vv_instance}")
        
        # Setup mock
        mock_instance = MockVibrationVIEW()
        mock_instance._demand_multiplier = 99.99
        print(f"Mock instance created: {id(mock_instance)}")
        print(f"Mock DemandMultiplier returns: {mock_instance.DemandMultiplier()}")
        
        # Set the singleton
        set_vv_instance(mock_instance)
        print(f"After set_vv_instance, _vv_instance: {id(_vv_instance) if _vv_instance else None}")
        
        # Test get_vv_instance directly
        retrieved_instance = get_vv_instance()
        print(f"Retrieved instance: {id(retrieved_instance) if retrieved_instance else None}")
        print(f"Is same as mock? {retrieved_instance is mock_instance}")
        
        if retrieved_instance:
            print(f"Retrieved instance DemandMultiplier: {retrieved_instance.DemandMultiplier()}")
        
        # Now test the route
        print("\n--- Testing route ---")
        response = client.get('/api/demandmultiplier')
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"Response data: {data}")
            actual_value = data['data']['result']
            print(f"Expected: 99.99, Actual: {actual_value}")
            
            # Check if DemandMultiplier was called on our mock
            print(f"Mock DemandMultiplier call count: {mock_instance.DemandMultiplier.call_count}")
        
        # Cleanup
        reset_vv_instance()

    def test_route_import_behavior(self, client):
        """Test to see how routes import get_vv_instance"""
        
        # Let's see what happens if we create an instance before setting our mock
        print("=== Testing route import behavior ===")
        
        # First, call the route without our mock to see what it does
        response1 = client.get('/api/demandmultiplier')
        print(f"Response without mock: {response1.status_code}")
        if response1.status_code == 200:
            data1 = json.loads(response1.data)
            print(f"Default value: {data1['data']['result']}")
        
        # Check the singleton state
        from app import _vv_instance
        print(f"Singleton after first call: {type(_vv_instance) if _vv_instance else None}")
        
        # Now try to set our mock
        mock_instance = MockVibrationVIEW()
        mock_instance._demand_multiplier = 123.45
        set_vv_instance(mock_instance)
        
        # Test again
        response2 = client.get('/api/demandmultiplier')
        print(f"Response with mock set: {response2.status_code}")
        if response2.status_code == 200:
            data2 = json.loads(response2.data)
            print(f"After setting mock: {data2['data']['result']}")
        
        reset_vv_instance()

    # Alternative approach: Reset before setting mock
    def test_reset_then_set_mock(self, client):
        """Test resetting singleton before setting mock"""
        
        # Force reset first
        reset_vv_instance()
        
        # Verify it's actually reset
        from app import _vv_instance
        print(f"After reset: {_vv_instance}")
        
        # Now set our mock
        mock_instance = MockVibrationVIEW()
        mock_instance._demand_multiplier = 555.55
        set_vv_instance(mock_instance)
        
        # Verify our mock is set
        from app import get_vv_instance
        instance = get_vv_instance()
        print(f"Instance after setting mock: {type(instance)}")
        print(f"Is our mock? {instance is mock_instance}")
        
        if instance:
            print(f"Instance DemandMultiplier: {instance.DemandMultiplier()}")
        
        # Test the route
        response = client.get('/api/demandmultiplier')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        print(f"Route response: {data}")
        
        actual_value = data['data']['result']
        print(f"Expected: 555.55, Actual: {actual_value}")
        
        # This should work now
        assert actual_value == 555.55
        
        reset_vv_instance()