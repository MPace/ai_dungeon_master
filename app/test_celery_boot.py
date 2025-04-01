from app import create_app
from app.celery_config import make_celery
import app.tasks

app = create_app()
celery = make_celery(app)

print("Tasks loaded:", celery.tasks.keys())
