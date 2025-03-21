import os
from flask import Flask
from app.extensions import init_extensions

def create_app(config_name=None):
    """
    Application factory function that creates and configures the Flask app
    """
    # Create the Flask application instance
    app = Flask(__name__)
    
    # Configure the application
    configure_app(app, config_name)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Additional setup needed at app startup
    # Setup directories that might be needed
    setup_directories(app)
    
    return app

def configure_app(app, config_name):
    """Configure the app with the appropriate settings"""
    # Default to development if not specified
    if not config_name:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    # Load config from config.py
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Load .env file if exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
    
    # Override with environment variables prefixed with 'AIDM_'
    for key, value in os.environ.items():
        if key.startswith('AIDM_'):
            app.config[key[5:]] = value

def register_blueprints(app):
    """Register Flask blueprints"""
    # Import blueprints
    from app.auth import auth_bp
    from app.characters import characters_bp
    from app.game import game_bp
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(characters_bp)
    app.register_blueprint(game_bp)

def register_error_handlers(app):
    """Register error handlers"""
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

def setup_directories(app):
    """Ensure necessary directories exist"""
    os.makedirs(app.static_folder + '/css', exist_ok=True)
    os.makedirs(app.static_folder + '/js', exist_ok=True)
    os.makedirs(app.static_folder + '/images', exist_ok=True)