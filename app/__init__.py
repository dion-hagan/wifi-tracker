from flask import Flask
from flask_cors import CORS

from app.config.logging_config import setup_logging
from app.api.routes import api, init_routes

def create_app(wifi_monitor=None):
    """Application factory function"""
    # Setup logging
    logger = setup_logging()
    
    # Create Flask app
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api)
    
    # Initialize routes with monitor if provided
    if wifi_monitor:
        init_routes(wifi_monitor)
    
    return app
