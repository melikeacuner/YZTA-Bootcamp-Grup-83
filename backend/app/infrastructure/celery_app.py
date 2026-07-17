from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("proby_ai", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_default_retry_delay = settings.embedding_retry_interval_seconds
