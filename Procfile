web: uv run gunicorn sisyphus.wsgi --bind 0.0.0.0:${PORT:-8000}
worker: uv run celery -A sisyphus worker -l info
beat: uv run celery -A sisyphus beat -l info
