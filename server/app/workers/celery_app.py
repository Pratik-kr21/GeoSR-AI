import os
from celery import Celery
from app.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.task_routes = {
    "app.workers.tasks.*": {"queue": "geosrai_queue"}
}

celery_app.conf.update(task_track_started=True)
