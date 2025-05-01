from flask import Flask, jsonify, request
import os
import logging
from datetime import datetime
from flask_swagger_ui import get_swaggerui_blueprint

# Import configuration
from config import API_PORT, DEBUG

# Import database initialization
from database.models import initialize_database
from database.db_manager import DatabaseManager

# Import API routes
from api.routes import api
from api.middleware import Middleware

# Import logger
from utils.logger import Logger

# Create Flask application
app = Flask(__name__)

# Configure Swagger UI
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Our API url (can be a local file or url)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "All-in-One Subsidy Platform API"
    }
)

# Register blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Setup logger
logger = Logger.setup_logger()

# Initialize database at startup
try:
    initialize_database()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Error initializing database: {e}")


# Add CORS headers to all responses
@app.after_request
def after_request(response):
    return Middleware.cors_headers(response)


# Handle OPTIONS requests
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return Middleware.options_handler()


# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'name': 'All-in-One Subsidy Platform API',
        'version': '1.0.0',
        'status': 'running',
        'timestamp': datetime.now().isoformat()
    })


# Health check endpoint
@app.route('/health')
def health_check():
    # Check database connection
    db_status = "ok"
    try:
        DatabaseManager.execute_query("SELECT 1")
    except Exception as e:
        db_status = f"error: {str(e)}"
        logger.error(f"Database health check failed: {e}")

    return jsonify({
        'status': 'healthy' if db_status == "ok" else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'api': 'ok',
            'database': db_status
        }
    })


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_server_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({'message': 'Internal server error'}), 500


# Shutdown handler
@app.teardown_appcontext
def shutdown_session(exception=None):
    DatabaseManager.close_all_connections()


if __name__ == '__main__':
    # Log startup
    logger.info(f"Starting All-in-One Subsidy Platform API on port {API_PORT}")

    # Run application
    app.run(host='0.0.0.0', port=API_PORT, debug=DEBUG)
