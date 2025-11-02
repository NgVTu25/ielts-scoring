import os
from celery import Celery

# Lấy Redis URL từ biến môi trường (Railway cung cấp)
REDIS_URL = os.getenv("CELERY_BROKER_URL")

celery_app = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)


celery = Celery(
    "worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.scoring"]
)

celery.conf.task_routes = {
    "app.services.scoring.*": {"queue": "default"},
}
