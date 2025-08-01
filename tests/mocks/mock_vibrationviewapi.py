from unittest.mock import MagicMock
import time
from typing import List, Dict, Any, Optional, Union

class MockVibrationVIEW:
    """
    Mock VibrationVIEW class that mimics the real vibrationviewapi.VibrationVIEW
    """

    def __init__(self):
        """Initialize the mock VibrationVIEW instance with default state"""
        self._is_ready = True
        self._is_running = False
        self._software_version = "2025.1.0"
        self._hardware_input_channels = 4
        self._hardware_output_channels = 2
        self._hardware_serial = "VV123456"
        self._test_type = 1
        self._current_test_file = None

        # Channel data
        self._channel_data = [1.0, 2.0, 3.0, 4.0]
        self._control_data = [0.5, 0.6]
        self._demand_data = [1.5, 1.6]
        self._output_data = [2.5, 2.6]

        # Test parameters
        self._demand_multiplier = 0.0
        self._sine_frequency = 100.0
        self._sweep_multiplier = 1.0
        self._system_check_frequency = 50.0
        self._system_check_output_voltage = 5.0

        # Status tracking
        self._status = {"stop_code": 0, "stop_code_index": 0}
        self._report_fields = {}

        # For tracking method calls
        self.method_calls = []

        # Connection state
        self._connected = False

        # Initialize all MagicMock methods
        self._init_magic_mocks()

    def _init_magic_mocks(self):
        """Initialize all MagicMock methods"""
        # Existing methods
        self.RearInputLabel = MagicMock()
        self.RearInputUnit = MagicMock()
        self.Demand = MagicMock()
        self.Control = MagicMock()
        self.Channel = MagicMock()
        self.Output = MagicMock()
        self.Vector = MagicMock()
        self.DemandMultiplier = MagicMock(side_effect=lambda: self._demand_multiplier)
        self.StartTest = MagicMock(return_value=True)
        self.StopTest = MagicMock(return_value=True)
        self.IsReady = MagicMock(side_effect=lambda: self._is_ready)
        self.IsRunning = MagicMock(side_effect=lambda: self._is_running)
        self.Teds = MagicMock()
        self.GetHardwareInputChannels = MagicMock(return_value=4)
        self.GetHardwareOutputChannels = MagicMock(return_value=2)
        
        # Add missing vector properties methods
        self.ChannelUnit = MagicMock()
        self.ChannelLabel = MagicMock()
        self.ControlUnit = MagicMock()
        self.ControlLabel = MagicMock()
        self.VectorUnit = MagicMock()
        self.VectorLabel = MagicMock()
        self.VectorLength = MagicMock()

    def _log_call(self, method_name: str, *args, **kwargs):
        self.method_calls.append({
            'method': method_name,
            'args': args,
            'kwargs': kwargs,
            'timestamp': time.time()
        })

    def get_method_calls(self, method_name: Optional[str] = None) -> List[Dict]:
        """Get logged method calls for verification"""
        # Handle MagicMock methods
        magic_mock_methods = [
            "RearInputLabel", "RearInputUnit", "ChannelUnit", "ChannelLabel",
            "ControlUnit", "ControlLabel", "VectorUnit", "VectorLabel", 
            "VectorLength", "Teds"
        ]
        
        if method_name in magic_mock_methods:
            mock = getattr(self, method_name, None)
            if mock and isinstance(mock, MagicMock):
                return [{'method': method_name, 'args': call.args, 'kwargs': call.kwargs} for call in mock.call_args_list]
            return []

        # Handle regular method calls
        if method_name:
            return [call for call in self.method_calls if call['method'] == method_name]
        return self.method_calls.copy()

    def clear_method_calls(self):
        """Clear all method call history"""
        self.method_calls.clear()
        
        # Reset all MagicMock methods
        magic_mock_attrs = [
            'RearInputLabel', 'RearInputUnit', 'Demand', 'Control', 'Channel', 
            'Output', 'Vector', 'DemandMultiplier', 'StartTest', 'StopTest', 
            'IsReady', 'IsRunning', 'Teds', 'GetHardwareInputChannels', 
            'GetHardwareOutputChannels', 'ChannelUnit', 'ChannelLabel', 
            'ControlUnit', 'ControlLabel', 'VectorUnit', 'VectorLabel', 'VectorLength'
        ]
        
        for attr_name in magic_mock_attrs:
            attr = getattr(self, attr_name, None)
            if attr and isinstance(attr, MagicMock):
                attr.reset_mock()

    def reset_mock(self):
        """Reset the entire mock to initial state"""
        self.__init__()

    # Additional methods that might be needed
    def Connect(self):
        """Mock Connect method"""
        self._connected = True
        self._log_call('Connect')
        return True

    def Disconnect(self):
        """Mock Disconnect method"""
        self._connected = False
        self._log_call('Disconnect')
        return True

    def IsConnected(self):
        """Mock IsConnected method"""
        self._log_call('IsConnected')
        return self._connected

    def GetSoftwareVersion(self):
        """Mock GetSoftwareVersion method"""
        self._log_call('GetSoftwareVersion')
        return self._software_version

    def GetHardwareSerial(self):
        """Mock GetHardwareSerial method"""
        self._log_call('GetHardwareSerial')
        return self._hardware_serial

    def GetTestType(self):
        """Mock GetTestType method"""
        self._log_call('GetTestType')
        return self._test_type

    def SetTestType(self, test_type: int):
        """Mock SetTestType method"""
        self._test_type = test_type
        self._log_call('SetTestType', test_type)
        return True

    def LoadTestFile(self, filename: str):
        """Mock LoadTestFile method"""
        self._current_test_file = filename
        self._log_call('LoadTestFile', filename)
        return True

    def GetCurrentTestFile(self):
        """Mock GetCurrentTestFile method"""
        self._log_call('GetCurrentTestFile')
        return self._current_test_file

    def SetSineFrequency(self, frequency: float):
        """Mock SetSineFrequency method"""
        self._sine_frequency = frequency
        self._log_call('SetSineFrequency', frequency)
        return True

    def GetSineFrequency(self):
        """Mock GetSineFrequency method"""
        self._log_call('GetSineFrequency')
        return self._sine_frequency

    def SetSweepMultiplier(self, multiplier: float):
        """Mock SetSweepMultiplier method"""
        self._sweep_multiplier = multiplier
        self._log_call('SetSweepMultiplier', multiplier)
        return True

    def GetSweepMultiplier(self):
        """Mock GetSweepMultiplier method"""
        self._log_call('GetSweepMultiplier')
        return self._sweep_multiplier

    def SetSystemCheckFrequency(self, frequency: float):
        """Mock SetSystemCheckFrequency method"""
        self._system_check_frequency = frequency
        self._log_call('SetSystemCheckFrequency', frequency)
        return True

    def GetSystemCheckFrequency(self):
        """Mock GetSystemCheckFrequency method"""
        self._log_call('GetSystemCheckFrequency')
        return self._system_check_frequency

    def SetSystemCheckOutputVoltage(self, voltage: float):
        """Mock SetSystemCheckOutputVoltage method"""
        self._system_check_output_voltage = voltage
        self._log_call('SetSystemCheckOutputVoltage', voltage)
        return True

    def GetSystemCheckOutputVoltage(self):
        """Mock GetSystemCheckOutputVoltage method"""
        self._log_call('GetSystemCheckOutputVoltage')
        return self._system_check_output_voltage

    def GetStatus(self):
        """Mock GetStatus method"""
        self._log_call('GetStatus')
        return self._status.copy()

    def GetReportField(self, field_name: str):
        """Mock GetReportField method"""
        self._log_call('GetReportField', field_name)
        return self._report_fields.get(field_name, "")

    def SetReportField(self, field_name: str, value: str):
        """Mock SetReportField method"""
        self._report_fields[field_name] = value
        self._log_call('SetReportField', field_name, value)
        return True