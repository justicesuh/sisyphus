import os

from celery import Celery
from celery.fixups.django import DjangoWorkerFixup
from django.core.exceptions import SynchronousOnlyOperation

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sisyphus.settings')

# Patch Celery's Django fixup to handle Python 3.14's async detection.
# conn.close() is decorated with @async_unsafe in Django 6.0, and Python 3.14's
# event loop changes cause it to be incorrectly flagged as an async context.
_original_close_database = DjangoWorkerFixup._close_database


def _patched_close_database(self):
    try:
        _original_close_database(self)
    except SynchronousOnlyOperation:
        pass


DjangoWorkerFixup._close_database = _patched_close_database

app = Celery('sisyphus')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all installed apps
app.autodiscover_tasks()
