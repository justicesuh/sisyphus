web: uv run gunicorn sisyphus.wsgi --bind 0.0.0.0:8000
worker: env DJANGO_ALLOW_ASYNC_UNSAFE=true uv run manage.py rqworker --with-scheduler --max-jobs 128 --worker-class sisyphus.core.worker.MemoryLimitWorker default
