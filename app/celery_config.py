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
celery = Celery('app')

# Configure the broker and backend
celery.conf.update({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'enable_utc': True,
    'task_routes': {
        'tasks.process_dm_message': {'queue': 'dm_queue'},
        'tasks.generate_memory_summary': {'queue': 'memory_queue'},
        'tasks.find_similar_memories_task': {'queue': 'memory_queue'},
        'tasks.generate_embedding_task': {'queue': 'embedding_queue'},
        'tasks.store_memory_task': {'queue': 'memory_queue'},
        'tasks.retrieve_memories_task': {'queue': 'memory_queue'},
        'tasks.promote_to_long_term_task': {'queue': 'memory_queue'}  # Added this new task
    }
})

# This allows the worker to find the app
celery.conf.update(
    imports=['app.tasks']
)

# Load additional configuration from object
class CeleryConfig:
    task_serializer = 'json'
    accept_content = ['json']
    result_serializer = 'json'
    timezone = 'UTC'
    task_track_started = True
    task_time_limit = 300

#celery.config_from_object(CeleryConfig)

@celery.task(bind=True)
def debug_task(self):
    logger.info(f"Task ID: {self.request.id}")
    return "OK"

logger.info("Celery instance created")
