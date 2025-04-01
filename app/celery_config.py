"""
Celery configuration for AI Dungeon Master
"""
from app import create_app

# Create a Flask application instance
flask_app = create_app()

# Create Celery application
from celery import Celery

def make_celery(app):
    """Create and configure Celery app with Flask context"""
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# Create Celery instance
celery = make_celery(flask_app)