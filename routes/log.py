# ============================================================================
# FILE: routes/log.py (Log Routes)
# ============================================================================

"""
Log Routes - 1:1 VibrationVIEW COM Interface Mapping
Event log retrieval operations matching exact COM method signatures
"""

from flask import Blueprint, jsonify
from utils.vv_manager import with_vibrationview
from utils.response_helpers import success_response
from utils.decorators import handle_errors
from utils.utils import ParseVvTable
import logging

# Create blueprint
log_bp = Blueprint('log', __name__)

logger = logging.getLogger(__name__)


@log_bp.route('/docs/log', methods=['GET'])
def get_documentation():
    """Get log module documentation"""
    docs = {
        'module': 'log',
        'description': '1:1 mapping of VibrationVIEW COM log/event methods',
        'com_object': 'VibrationVIEW.Application',
        'endpoints': {
            'GET /log': {
                'description': 'Get event log from VibrationVIEW',
                'com_method': 'ReportField("Events")',
                'parameters': 'None',
                'returns': 'array - List of event log entries as objects',
                'example': 'GET /api/v1/log'
            }
        },
        'notes': [
            'Returns event log data parsed into structured objects',
            'Each event entry contains timestamp, type, and message fields'
        ]
    }
    return jsonify(docs)


@log_bp.route('/log', methods=['GET'])
@handle_errors
@with_vibrationview
def log(vv_instance):
    """
    Get Event Log

    COM Method: ReportField("Events")
    Returns the VibrationVIEW event log as a structured list.

    Example: GET /api/v1/log
    """
    events = vv_instance.ReportField('Events')
    parsed_events = ParseVvTable(events)

    return jsonify(success_response(
        {'events': parsed_events, 'count': len(parsed_events)},
        f"Event log retrieved: {len(parsed_events)} entries"
    ))
