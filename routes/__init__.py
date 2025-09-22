# ============================================================================
# FILE: routes/__init__.py (Package Initialization)
# ============================================================================

"""
Routes package for VibrationVIEW API

This package contains all the route modules organized by functionality.
"""

__version__ = '1.0.0'

# Import all blueprints for easy access
from .basic_control import basic_control_bp
from .status_properties import status_properties_bp
from .data_retrieval import data_retrieval_bp
from .advanced_control import advanced_control_bp
from .advanced_control_sine import advanced_control_sine_bp
from .advanced_control_system_check import advanced_control_system_check_bp
from .hardware_config import hardware_config_bp
from .input_config import input_config_bp
from .recording import recording_bp
from .teds import teds_bp
from .reporting import reporting_bp
from .aux_inputs import auxinputs_bp
from .gui_control import gui_control_bp
from .report_generation import report_generation_bp

__all__ = [
    'basic_control_bp',
    'status_properties_bp',
    'data_retrieval_bp',
    'advanced_control_bp',
    'advanced_control_sine_bp',
    'advanced_control_system_check_bp',
    'hardware_config_bp',
    'input_config_bp',
    'recording_bp',
    'teds_bp',
    'reporting_bp',
    'auxinputs_bp',
    'gui_control_bp',
    'report_generation_bp'
]