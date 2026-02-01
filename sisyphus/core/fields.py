from django.db import models


class AutoCreatedField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now_add', True)
        super().__init__(*args, **kwargs)


class AutoUpdatedField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now', True)
        super().__init__(*args, **kwargs)
