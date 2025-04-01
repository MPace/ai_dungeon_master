from app import create_app
from app.celery_config import make_celery

flask_app = create_app()
celery = make_celery(flask_app)