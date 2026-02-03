import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sisyphus.settings')

app = Celery('sisyphus')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()
