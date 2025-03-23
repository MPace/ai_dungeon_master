import os
from flask import Flask, render_template, redirect, url_for
import logging
from datetime import timedelta
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    app = Flask(__name__)   
    configure_app(app, config_name)

    # Initialize CSRF protection
    csrf = CSRFProtect(app)

    # Load configuration
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    logger.info(f"SECRET_KEY set to: {app.config['SECRET_KEY']}")

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.characters.routes import characters_bp
    from app.game.routes import game_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(characters_bp, url_prefix='/characters')
    app.register_blueprint(game_bp)  # No prefix to maintain compatibility with original URLs
    
    # Add a route for the root URL to maintain backward compatibility
    @app.route('/')
    def index():
        return redirect(url_for('auth.index'))
    
    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    return app

def configure_app(app, config_name):
    """Configure the app with the appropriate settings"""

    config_name = 'production'
    # Default to development if not specified
    if not config_name or config_name == 'default':
        config_name = 'development'
    
    
    # Load .env file if exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()

    # Load config from config.py
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Configure session
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_NAME'] = 'session_aidm'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/var/www/sessions'

    if config_name == 'production' and app.config['SESSION_TYPE'] == 'redis':
        import redis
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            app.config['SESSION_REDIS'] = redis.from_url(redis_url)
            logger.info("Using Redis for session storage")
        else:
            app.config['SESSION_TYPE'] = 'filesystem'
            logger.warning('Redis URL not found, falling back to filesystem sessions')

    Session(app)
    
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
    app.register_blueprint(characters_bp, url_prefix='/characters')
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