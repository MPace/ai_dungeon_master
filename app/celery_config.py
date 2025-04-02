"""
Celery configuration for AI Dungeon Master
"""
import os
from celery import Celery
import logging

logging.basicConfig(
    filename='/var/www/staging_ai_dungeon_master/app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
logger.info("celery_config.py is executing")

# Create Celery instance first
celery = Celery(
    'app',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    include=['app.tasks']
)

# Load additional configuration from object
class CeleryConfig:
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    task_track_started = True
    task_time_limit = 300

celery.config_from_object(CeleryConfig)

@celery.task(bind=True)
def debug_task(self):
    logger.info(f"Task ID: {self.request.id}")
    return "OK"

logger.info("Celery instance created")
