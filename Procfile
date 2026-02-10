web: uv run gunicorn sisyphus.wsgi --bind 0.0.0.0:8000
worker: uv run manage.py rqworker --with-scheduler default
