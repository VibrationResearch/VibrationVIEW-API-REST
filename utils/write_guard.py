# ============================================================================
# Write Guard - Block GET on state-changing endpoints
# ============================================================================

"""
When ALLOW_GET_WRITE is false, registers a before_request hook that returns
405 for GET requests to state-changing endpoints.
"""

from flask import jsonify, request

WRITE_ENDPOINTS = {
    "starttest",
    "runtest",
    "stoptest",
    "resumetest",
    "opentest",
    "closetest",
    "closetab",
    "savedata",
    "recordstart",
    "recordstop",
    "recordpause",
    "edittest",
    "abortedit",
    "minimize",
    "restore",
    "maximize",
    "activate",
    "removeallvirtualchannels",
    "importvirtualchannels",
    "generatereport",
    "generatetxt",
    "generateuff",
    "tedsreadandapply",
    "tedsread",
    "updatechannelconfigfromdatabase",
}


def register_write_guard(app, prefix="/api/v1"):
    """Register a before_request hook that blocks GET on write endpoints."""
    blocked = {f"{prefix}/{ep}" for ep in WRITE_ENDPOINTS}

    @app.before_request
    def block_get_on_write_endpoints():
        if request.method == "GET" and request.path in blocked:
            return jsonify(
                {
                    "success": False,
                    "error": "Method not allowed",
                    "message": "GET is not allowed on state-changing endpoints. Use POST instead.",
                }
            ), 405
