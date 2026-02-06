import uuid

from django.core.exceptions import ValidationError
from django.db import models


class AutoCreatedField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now_add', True)
        super().__init__(*args, **kwargs)


class AutoUpdatedField(models.DateTimeField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('auto_now', True)
        super().__init__(*args, **kwargs)


class UUIDField(models.UUIDField):
    def __init__(self, verbose_name=None, primary_key=False, version=4, editable=False, *args, **kwargs):
        if version == 2:
            raise ValidationError('UUID version 2 is not supported.')

        if version < 1 or version > 7:
            raise ValidationError('UUID version is not valid.')

        default = getattr(uuid, f'uuid{version}')

        kwargs.setdefault('verbose_name', verbose_name)
        kwargs.setdefault('primary_key', primary_key)
        kwargs.setdefault('default', default)
        kwargs.setdefault('editable', editable)
        super().__init__(*args, **kwargs)
