web: uv run gunicorn sisyphus.wsgi --bind 0.0.0.0:8000
worker: uv run celery -A sisyphus worker -l info --pool=prefork
beat: uv run celery -A sisyphus beat -l info
