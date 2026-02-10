import django_rq


@django_rq.job
def add(x: int, y: int) -> int:
    """Add two numbers to verify the worker is running."""
    return x + y


@django_rq.job
def ping() -> str:
    """Return pong as a health check."""
    return 'pong'
