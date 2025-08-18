# ============================================================================
# FILE: app.py (Main Application - Updated with Singleton)
# ============================================================================

"""
VibrationVIEW Flask REST API - Main Application

Entry point for the modular VibrationVIEW automation interface.
"""

from flask import Flask, jsonify
from flask_cors import CORS
import logging
import os
from datetime import datetime
import threading

# Import route modules - clean imports using __init__.py
from routes import ( 
    basic_control_bp,
    status_properties_bp,
    data_retrieval_bp,
    advanced_control_bp,
    advanced_control_sine_bp,
    advanced_control_system_check_bp,
    hardware_config_bp,
    input_config_bp,
    teds_bp,
    recording_bp,
    reporting_bp,
    auxinputs_bp,
    gui_control_bp
)

# Import configuration
from config import Config

# Global singleton instance and lock
_vv_instance = None
_vv_lock = threading.Lock()

def get_vv_instance():
    """Get VibrationVIEW instance - thread-safe singleton"""
    global _vv_instance
    
    if _vv_instance is not None:
        return _vv_instance
    
    with _vv_lock:
        # Double-check locking pattern
        if _vv_instance is not None:
            return _vv_instance
            
        try:
            from vibrationviewapi import VibrationVIEW
            vv_instance = VibrationVIEW()
            
            if vv_instance.vv is None:
                print("Failed to connect to VibrationVIEW")
                return None
                
            _vv_instance = vv_instance
            print("VibrationVIEW singleton instance created successfully")
            return _vv_instance
            
        except ImportError as e:
            print(f"Could not import VibrationVIEW API: {e}")
            return None
        except Exception as e:
            print(f"Error connecting to VibrationVIEW: {e}")
            return None

def set_vv_instance(instance):
    """Set the VibrationVIEW instance - useful for testing"""
    global _vv_instance
    with _vv_lock:
        _vv_instance = instance

def reset_vv_instance():
    """Reset the VibrationVIEW instance - useful for testing cleanup"""
    global _vv_instance
    with _vv_lock:
        _vv_instance = None

def create_app(config_class=Config):
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', '*'),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configure logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.FileHandler('logs/api.log'),
            logging.StreamHandler()
        ]
    )
    
    # Register blueprint modules directly under /api/ (no module prefixes)
    app.register_blueprint(basic_control_bp, url_prefix='/api')
    app.register_blueprint(status_properties_bp, url_prefix='/api')
    app.register_blueprint(data_retrieval_bp, url_prefix='/api')
    app.register_blueprint(advanced_control_bp, url_prefix='/api')
    app.register_blueprint(advanced_control_sine_bp, url_prefix='/api')
    app.register_blueprint(advanced_control_system_check_bp, url_prefix='/api')
    app.register_blueprint(hardware_config_bp, url_prefix='/api')
    app.register_blueprint(input_config_bp, url_prefix='/api')
    app.register_blueprint(teds_bp, url_prefix='/api')
    app.register_blueprint(recording_bp, url_prefix='/api')
    app.register_blueprint(reporting_bp, url_prefix='/api')
    app.register_blueprint(auxinputs_bp, url_prefix='/api')
    app.register_blueprint(gui_control_bp, url_prefix='/api')

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        vv = get_vv_instance()
        vv_status = "connected" if vv is not None else "disconnected"
        
        return jsonify({
            'success': True,
            'message': 'VibrationVIEW API is running',
            'version': app.config.get('API_VERSION', '1.0.0'),
            'timestamp': datetime.now().isoformat(),
            'vibrationview_status': vv_status,
            'modules': [
                'basic_control',
                'status_properties', 
                'data_retrieval',
                'advanced_control',
                'advanced_control_sine',
                'advanced_control_system_check',
                'hardware_config',
                'input_config',
                'teds',
                'recording',
                'reporting',
                'auxinputs',
                'gui_control'
            ],
            'endpoints': [
                'POST /api/starttest',
                'POST /api/runtest', 
                'POST /api/stoptest',
                'POST /api/pausetest',
                'POST /api/resumetest',
                'POST /api/opentest'
            ]
        })
    
    # Testing helper endpoint (only in debug mode)
    @app.route('/api/test/reset-instance', methods=['POST'])
    def reset_instance():
        """Reset VibrationVIEW instance - for testing only"""
        if not app.debug:
            return jsonify({
                'success': False,
                'error': 'Not available in production mode'
            }), 403
            
        reset_vv_instance()
        return jsonify({
            'success': True,
            'message': 'VibrationVIEW instance reset'
        })
    
    # Main API documentation endpoint
    @app.route('/api/docs', methods=['GET'])
    def api_documentation():
        """Get comprehensive API documentation"""
        from flask import request
        
        docs = {
            'title': 'VibrationVIEW REST API - Modular 1:1 Automation Interface',
            'version': app.config.get('API_VERSION', '1.0.0'),
            'description': 'Exact 1:1 REST interface for VibrationVIEW COM automation methods',
            'base_url': request.host_url + 'api',
            'architecture': 'Modular design with functional separation and singleton VibrationVIEW instance',
            'modules': {
                'basic_control': 'Core test control operations (StartTest, StopTest, etc.)',
                'status_properties': 'System status and state checking',
                'data_retrieval': 'Real-time data access (Channel, Demand, etc.)',
                'advanced_control': 'Advanced test control (parameters, non-sine)',
                'advanced_control_sine': 'Sine-specific advanced control (sweep operations)',
                'advanced_control_system_check': 'System check operations (frequency, output voltage)',
                'hardware_config': 'Hardware information and capability checks',
                'input_config': 'Input channel properties, settings, and configuration',
                'teds': 'TEDS (Transducer Electronic Data Sheet) information',
                'recording': 'Recorder Control',
                'reporting': 'Reporting parameters',
                'auxinputs': 'Aux Inputs parameters',
                'gui_control': 'GUI and window management operations'
            },
            'module_docs': {
                'basic_control': request.host_url + 'api/docs/basic_control',
                'status_properties': request.host_url + 'api/docs/status_properties',
                'data_retrieval': request.host_url + 'api/docs/data_retrieval',
                'advanced_control': request.host_url + 'api/docs/advanced_control',
                'advanced_control_sine': request.host_url + 'api/docs/advanced_control_sine',
                'advanced_control_system_check': request.host_url + 'api/docs/advanced_control_system_check',
                'hardware_config': request.host_url + 'api/docs/hardware_config',
                'input_config': request.host_url + 'api/docs/input_config',
                'teds': request.host_url + 'api/docs/teds', 
                'recording': request.host_url + 'api/docs/recording', 
                'reporting': request.host_url + 'api/docs/reporting', 
                'auxinputs': request.host_url + 'api/docs/auxinputs',
                'gui_control': request.host_url + 'api/docs/gui_control'
            }
        }
        
        return jsonify(docs)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'message': 'The requested API endpoint does not exist',
            'available_docs': '/api/docs'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method not allowed',
            'message': 'The HTTP method is not allowed for this endpoint'
        }), 405

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 'Bad request',
            'message': 'Invalid request parameters'
        }), 400

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return app

if __name__ == '__main__':
    # Simple connection test
    print("Testing VibrationVIEW connection...")
    test_instance = get_vv_instance()
    if test_instance is None:
        print("Failed to initialize VibrationVIEW. Exiting.")
        exit(-1)
    else:
        print("VibrationVIEW connection test successful")
    
    # Create and run app
    print("Starting Flask server...")
    app = create_app()
    
    import argparse
    
    parser = argparse.ArgumentParser(description='VibrationVIEW Flask REST API')
    parser.add_argument('--host', default='127.0.0.1', help='Host address')
    parser.add_argument('--port', type=int, default=5000, help='Port number')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='development', help='Configuration environment')
    
    args = parser.parse_args()
    
    app.logger.info(f"Starting VibrationVIEW API server on {args.host}:{args.port}")
    app.logger.info(f"Configuration: {args.config}")
    app.logger.info(f"API documentation: http://{args.host}:{args.port}/api/docs")
    app.logger.info(f"Basic control docs: http://{args.host}:{args.port}/api/docs/basic_control")
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Server error: {e}")
        raise