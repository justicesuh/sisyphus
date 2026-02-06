from celery import shared_task


@shared_task
def add(x: int, y: int) -> int:
    """Add two numbers to verify Celery is working."""
    return x + y


@shared_task
def ping() -> str:
    """Return pong as a health check."""
    return 'pong'
