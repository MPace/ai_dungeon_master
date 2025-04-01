"""
Celery configuration for AI Dungeon Master
"""
import os
from celery import Celery
import logging
logger = logging.getLogger(__name__)
logger.info("celery_config.py is executing")

def make_celery(app):
    """Create and configure Celery app with Flask context"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'],
        include=['app.tasks']  
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    import app.tasks
    logger.info("app.tasks module imported in celery_config")
    return celery

# Create a Flask application instance
from app import create_app
flask_app = create_app()
logger.info("Flask app created")

# Create Celery instance
celery = make_celery(flask_app)
logger.info("Celery instance created")
celery.autodiscover_tasks(['app'])

