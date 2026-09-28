#!/bin/bash
exec celery -A app.workers.celery_app worker --loglevel=info -Q geosrai_queue --pool=solo
