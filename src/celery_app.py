from celery import Celery
from src.config.settings import get_redis_url

redis_url = get_redis_url()


celery_app = Celery(
    "reddit",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.timezone = "UTC"
celery_app.autodiscover_tasks(['src.tasks', 'src.tasks.hi', 'src.tasks.send_email'])
