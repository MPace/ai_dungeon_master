#!/bin/bash
cd /var/www/staging_ai_dungeon_master
source /mnt/volume_sf03_01/venv/bin/activate
celery -A app.celery_config.celery worker --loglevel=info