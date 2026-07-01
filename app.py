# ============================================================================
# FILE: app.py (Main Application - Updated with Singleton)
# ============================================================================

"""
VibrationVIEW Flask REST API - Main Application

Entry point for the modular VibrationVIEW automation interface.
"""

import hmac
import logging
import math
import os
from datetime import datetime, timezone
from typing import Any, Optional

from flask import Flask, Response, jsonify
from flask import request as flask_request
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

# Module-level logger
logger = logging.getLogger(__name__)

# Import route modules and configuration
from config import Config
from routes import (
    advanced_control_bp,
    advanced_control_sine_bp,
    advanced_control_system_check_bp,
    auxinputs_bp,
    basic_control_bp,
    data_retrieval_bp,
    gui_control_bp,
    hardware_config_bp,
    input_config_bp,
    log_bp,
    recording_bp,
    report_generation_bp,
    reporting_bp,
    status_properties_bp,
    teds_bp,
    vectors_legacy_bp,
    virtual_channels_bp,
)
from utils.vv_singleton import get_vv_instance, reset_vv_instance, set_vv_instance  # noqa: F401


def _sanitize_nan(value: Any) -> Any:
    """Replace NaN and Inf float values with None for JSON serialization."""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    elif isinstance(value, dict):
        return {k: _sanitize_nan(v) for k, v in value.items()}
    elif isinstance(value, (list, tuple)):
        return [_sanitize_nan(v) for v in value]
    return value


class _NaNSafeJSONProvider(DefaultJSONProvider):
    """JSON provider that converts NaN and Inf floats to null."""

    def dumps(self, obj: Any, **kwargs: Any) -> str:
        return super().dumps(_sanitize_nan(obj), **kwargs)


def create_app(config_class=Config) -> Flask:
    """Application factory"""

    app = Flask(__name__)
    app.json = _NaNSafeJSONProvider(app)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(
        app,
        resources={
            r"/api/v1/*": {
                "origins": app.config.get("CORS_ORIGINS", "*"),
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Configure logging — use an absolute log directory so logs are not
    # scattered when the service is started from different directories.
    from logging.handlers import RotatingFileHandler

    log_dir = app.config["VV_LOG_DIR"]
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "api.log")
    max_bytes = app.config["VV_LOG_MAX_BYTES"]
    backup_count = app.config["VV_LOG_BACKUP_COUNT"]

    # Clear any existing handlers to ensure basicConfig takes effect
    logging.root.handlers = []
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO")),
        format="%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
        handlers=[RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count), logging.StreamHandler()],
    )

    # Warn about missing paths (runs in all modes including flask run).
    for warning in Config.validate_paths():
        logger.warning(f"\033[91m{warning}\033[0m")

    # API key authentication — uses @app.before_request for global Bearer token check.
    # Alternative: Flask-HTTPAuth (pip install Flask-HTTPAuth) provides a cleaner
    # decorator-based approach (HTTPTokenAuth) with built-in Bearer parsing and
    # easier extensibility for multiple keys or roles.
    # tradeoff: custom implementation avoids extra dependencies and is straightforward for single-key use case.
    from config import _DEV_SECRET_KEY, _PLACEHOLDER_API_KEY

    if app.config.get("SECRET_KEY") == _DEV_SECRET_KEY:
        logger.warning(
            "\033[91mSECRET_KEY is the development default. Set a secure value in .env before deploying.\033[0m"
        )

    api_key = app.config.get("API_KEY", "")
    if not api_key:
        logger.warning("\033[91mAPI_KEY is not set. Set a strong, unique API_KEY in .env before deploying.\033[0m")
    if api_key:
        if api_key == _PLACEHOLDER_API_KEY:
            logger.warning(
                "\033[91mUsing placeholder API key for authentication. "
                "Replace with a strong, unique key before deploying.\033[0m"
            )

        @app.before_request
        def require_api_key() -> Optional[Response]:
            # Allow health and docs endpoints without authentication
            parts = flask_request.path.rstrip("/").split("/")
            # parts: ['', 'api', 'vN', '<resource>', ...]
            resource = parts[3] if len(parts) > 3 else ""
            if resource in ("health", "docs"):
                return
            auth = flask_request.headers.get("Authorization", "")
            if auth.startswith("Bearer "):
                token = auth[7:]
            else:
                token = auth
            if not hmac.compare_digest(token, api_key):
                return jsonify(
                    {
                        "success": False,
                        "error": "Unauthorized",
                        "message": "Valid API key required in Authorization header",
                    }
                ), 401

    # Block GET on state-changing endpoints unless ALLOW_GET_WRITE is true
    if not app.config.get("ALLOW_GET_WRITE", True):
        from utils.write_guard import register_write_guard

        register_write_guard(app)

    # Register blueprint modules directly under /api/v1/ (no module prefixes)
    app.register_blueprint(basic_control_bp, url_prefix="/api/v1")
    app.register_blueprint(status_properties_bp, url_prefix="/api/v1")
    app.register_blueprint(data_retrieval_bp, url_prefix="/api/v1")
    app.register_blueprint(advanced_control_bp, url_prefix="/api/v1")
    app.register_blueprint(advanced_control_sine_bp, url_prefix="/api/v1")
    app.register_blueprint(advanced_control_system_check_bp, url_prefix="/api/v1")
    app.register_blueprint(hardware_config_bp, url_prefix="/api/v1")
    app.register_blueprint(input_config_bp, url_prefix="/api/v1")
    app.register_blueprint(teds_bp, url_prefix="/api/v1")
    app.register_blueprint(recording_bp, url_prefix="/api/v1")
    app.register_blueprint(reporting_bp, url_prefix="/api/v1")
    app.register_blueprint(auxinputs_bp, url_prefix="/api/v1")
    app.register_blueprint(gui_control_bp, url_prefix="/api/v1")
    app.register_blueprint(report_generation_bp, url_prefix="/api/v1")
    app.register_blueprint(virtual_channels_bp, url_prefix="/api/v1")
    app.register_blueprint(log_bp, url_prefix="/api/v1")
    app.register_blueprint(vectors_legacy_bp, url_prefix="/api/v1")

    # Health check endpoint
    @app.route("/api/v1/health", methods=["GET"])
    def health_check() -> Response:
        """Health check endpoint"""
        vv = get_vv_instance()
        connection = {"success": False, "error": None}
        if vv is not None:
            try:
                from utils.utils import get_hardware_info

                connection = get_hardware_info(vv)
            except Exception as e:
                from utils.vv_error_codes import format_com_error

                connection.update(format_com_error(e))

        return jsonify(
            {
                "success": True,
                "message": "VibrationVIEW API is running",
                "version": app.config.get("API_VERSION", "1.0.0"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "vibrationview_connection": connection,
                "modules": [
                    "basic_control",
                    "status_properties",
                    "data_retrieval",
                    "advanced_control",
                    "advanced_control_sine",
                    "advanced_control_system_check",
                    "hardware_config",
                    "input_config",
                    "teds",
                    "recording",
                    "reporting",
                    "auxinputs",
                    "gui_control",
                    "virtual_channels",
                    "log",
                ],
                "endpoints": [
                    "POST /api/v1/starttest",
                    "POST /api/v1/runtest",
                    "POST /api/v1/stoptest",
                    "POST /api/v1/pausetest",
                    "POST /api/v1/resumetest",
                    "POST /api/v1/opentest",
                ],
            }
        )

    # Testing helper endpoint (only in debug mode)
    @app.route("/api/v1/test/reset-instance", methods=["POST"])
    def reset_instance() -> Response:
        """Reset VibrationVIEW instance - for testing only"""
        if not app.debug:
            return jsonify({"success": False, "error": "Not available in production mode"}), 403

        reset_vv_instance()
        return jsonify({"success": True, "message": "VibrationVIEW instance reset"})

    # Main API documentation endpoint
    @app.route("/api/v1/docs", methods=["GET"])
    def api_documentation() -> Response:
        """Get comprehensive API documentation"""
        from flask import request

        docs = {
            "title": "VibrationVIEW REST API - Modular 1:1 Automation Interface",
            "version": app.config.get("API_VERSION", "1.0.0"),
            "description": "Exact 1:1 REST interface for VibrationVIEW COM automation methods",
            "base_url": request.host_url + "api/v1",
            "architecture": "Modular design with functional separation and singleton VibrationVIEW instance",
            "modules": {
                "basic_control": "Core test control operations (StartTest, StopTest, etc.)",
                "status_properties": "System status and state checking",
                "data_retrieval": "Real-time data access (Channel, Demand, etc.)",
                "advanced_control": "Advanced test control (parameters, non-sine)",
                "advanced_control_sine": "Sine-specific advanced control (sweep operations)",
                "advanced_control_system_check": "System check operations (frequency, output voltage)",
                "hardware_config": "Hardware information and capability checks",
                "input_config": "Input channel properties, settings, and configuration",
                "teds": "TEDS (Transducer Electronic Data Sheet) information",
                "recording": "Recorder Control",
                "reporting": "Reporting parameters",
                "auxinputs": "Aux Inputs parameters",
                "gui_control": "GUI and window management operations",
                "virtual_channels": "Virtual channel management (import, remove)",
                "log": "Event log retrieval",
            },
            "module_docs": {
                "basic_control": request.host_url + "api/v1/docs/basic_control",
                "status_properties": request.host_url + "api/v1/docs/status_properties",
                "data_retrieval": request.host_url + "api/v1/docs/data_retrieval",
                "advanced_control": request.host_url + "api/v1/docs/advanced_control",
                "advanced_control_sine": request.host_url + "api/v1/docs/advanced_control_sine",
                "advanced_control_system_check": request.host_url + "api/v1/docs/advanced_control_system_check",
                "hardware_config": request.host_url + "api/v1/docs/hardware_config",
                "input_config": request.host_url + "api/v1/docs/input_config",
                "teds": request.host_url + "api/v1/docs/teds",
                "recording": request.host_url + "api/v1/docs/recording",
                "reporting": request.host_url + "api/v1/docs/reporting",
                "auxinputs": request.host_url + "api/v1/docs/auxinputs",
                "gui_control": request.host_url + "api/v1/docs/gui_control",
                "virtual_channels": request.host_url + "api/v1/docs/virtual_channels",
                "log": request.host_url + "api/v1/docs/log",
            },
        }

        return jsonify(docs)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error: Exception) -> Response:
        return jsonify(
            {
                "success": False,
                "error": "Endpoint not found",
                "message": "The requested API endpoint does not exist",
                "available_docs": "/api/v1/docs",
            }
        ), 404

    @app.errorhandler(405)
    def method_not_allowed(error: Exception) -> Response:
        return jsonify(
            {
                "success": False,
                "error": "Method not allowed",
                "message": "The HTTP method is not allowed for this endpoint",
            }
        ), 405

    @app.errorhandler(400)
    def bad_request(error: Exception) -> Response:
        return jsonify({"success": False, "error": "Bad request", "message": "Invalid request parameters"}), 400

    @app.errorhandler(413)
    def request_entity_too_large(error: Exception) -> Response:
        max_mb = app.config.get("MAX_CONTENT_LENGTH", 0) // (1024 * 1024)
        return jsonify(
            {
                "success": False,
                "error": "Request entity too large",
                "message": f"Request body exceeds the {max_mb}MB limit",
            }
        ), 413

    @app.errorhandler(500)
    def internal_error(error: Exception) -> Response:
        return jsonify(
            {"success": False, "error": "Internal server error", "message": "An unexpected error occurred"}
        ), 500

    # Try to connect at startup, but allow the app to start without VibrationVIEW.
    # The singleton will retry on each request via get_vv_instance().
    logger.info("Attempting VibrationVIEW connection...")
    vv = get_vv_instance()
    if vv is None:
        logger.warning("VibrationVIEW not available at startup — will retry on first request")
    else:
        logger.info("VibrationVIEW connection established successfully")

    return app


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="VibrationVIEW Flask REST API")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Validate configuration before starting in production mode.
    # print() used here because logging is not configured until create_app() runs.
    # Mutate Config class attributes before create_app() so the factory
    # picks up debug settings.  Only runs from the CLI entry point;
    # tests use TestingConfig and are unaffected.
    if args.debug:
        Config.DEBUG = True
        Config.LOG_LEVEL = "DEBUG"
    else:
        try:
            Config.validate_production()
        except RuntimeError as e:
            print(f"Failed to initialize: {e}")
            exit(-1)

    print("Starting Flask server...")
    app = create_app()

    logger.info(f"Starting VibrationVIEW API server on {args.host}:{args.port}")
    logger.info(f"API documentation: http://{args.host}:{args.port}/api/v1/docs")
    logger.info(f"Basic control docs: http://{args.host}:{args.port}/api/v1/docs/basic_control")

    def shutdown():
        logger.info("Shutting down — releasing VibrationVIEW COM object...")
        reset_vv_instance()
        logger.info("Shutdown complete.")

    try:
        if args.debug:
            app.run(host=args.host, port=args.port, debug=True, threaded=False)
        else:
            from waitress import serve  # type: ignore[import-untyped]

            logger.info(f"Serving with Waitress on http://{args.host}:{args.port}")
            serve(app, host=args.host, port=args.port, threads=1)
    except KeyboardInterrupt:
        logger.info("Ctrl+C received.")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        shutdown()
