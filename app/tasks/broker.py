from taskiq_redis import ListQueueBroker

from app.config import settings

broker = ListQueueBroker(settings.redis_url)
