from celery import shared_task


@shared_task
def add(x, y):
    """Simple task to verify Celery is working."""
    return x + y


@shared_task
def ping():
    """Health check task."""
    return 'pong'
