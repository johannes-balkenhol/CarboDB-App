import os

from redis import Redis
from rq import Queue


REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PREDICT_QUEUE_NAME = os.environ.get("PREDICT_QUEUE_NAME", "predict")
BATCH_QUEUE_NAME = os.environ.get("BATCH_QUEUE_NAME", "batch")


def get_redis_connection() -> Redis:
    """
    Return a Redis connection used by FastAPI routes and RQ workers.
    """
    return Redis.from_url(REDIS_URL)


def get_predict_queue() -> Queue:
    """
    Return the RQ queue for single-sequence prediction jobs.
    """
    return Queue(
        name=PREDICT_QUEUE_NAME,
        connection=get_redis_connection(),
        default_timeout=int(os.environ.get("PREDICT_JOB_TIMEOUT", "300")),
        result_ttl=int(os.environ.get("PREDICT_RESULT_TTL", "3600")),
        failure_ttl=int(os.environ.get("PREDICT_FAILURE_TTL", "86400")),
    )

def get_batch_queue() -> Queue:
    """
    Return the RQ queue for batch prediction jobs.
    """
    return Queue(
        name=BATCH_QUEUE_NAME,
        connection=get_redis_connection(),
        default_timeout=int(os.environ.get("BATCH_JOB_TIMEOUT", "3600")),
        result_ttl=int(os.environ.get("BATCH_RESULT_TTL", "86400")),
        failure_ttl=int(os.environ.get("BATCH_FAILURE_TTL", "86400")),
    )