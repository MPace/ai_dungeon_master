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

    with app.app_context():
        try:
            from app.mcp import init_mcp
            init_mcp()
            logger.info("MCP initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MCP: {e}")


    # Initialize CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)

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

    config_name = os.environ.get('FLASK_ENV', config_name)
    # Default to development if not specified
    if not config_name or config_name == 'default':
        config_name = 'development'
    
    # Load .env file if exists
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()

    # Load config from config.py
    app.config.from_object(f'app.config.{config_name.capitalize()}Config')
    
    # Set SECRET_KEY
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', os.urandom(24))
    
    # Configure session
    app.config['SESSION_TYPE'] = 'filesystem'
    
    # Configure session cookies
    app.config['SESSION_COOKIE_NAME'] = 'aidm_session'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
    
    # Security settings - adjust based on environment
    if config_name == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True  # Requires HTTPS
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Changed from 'Strict' to 'Lax' for better compatibility
    else:
        # Development environment - less strict for easier testing
        app.config['SESSION_COOKIE_SECURE'] = False  # Works without HTTPS
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Create the session directory if using filesystem sessions
    if app.config['SESSION_TYPE'] == 'filesystem':
        session_dir = os.environ.get('SESSION_FILE_DIR', '/tmp/flask_sessions')
        app.config['SESSION_FILE_DIR'] = session_dir
        os.makedirs(session_dir, exist_ok=True)
        logger.info(f"Using filesystem sessions at {session_dir}")
    
    # Redis session support
    if config_name == 'production' and os.environ.get('REDIS_URL'):
        try:
            import redis
            app.config['SESSION_TYPE'] = 'redis'
            app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL'))
            logger.info("Using Redis for session storage")
        except (ImportError, Exception) as e:
            logger.warning(f'Could not configure Redis sessions: {e}')
            logger.warning('Falling back to filesystem sessions')
    
    # Initialize session extension
    Session(app)
    
    # Set up CSRF protection
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['WTF_CSRF_SSL_STRICT'] = False  # Important for dev environments
    
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
