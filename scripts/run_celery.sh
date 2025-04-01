#!/bin/bash
cd /var/www/staging_ai_dungeon_master
source /mnt/volume_sfo3_01/venv/bin/activate
celery -A app.celery_app.celery worker --loglevel=debug