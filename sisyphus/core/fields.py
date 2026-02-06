import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models


class AutoCreatedField(models.DateTimeField):
    """DateTimeField that automatically sets to now on creation."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault('auto_now_add', True)
        super().__init__(*args, **kwargs)


class AutoUpdatedField(models.DateTimeField):
    """DateTimeField that automatically updates to now on save."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault('auto_now', True)
        super().__init__(*args, **kwargs)


class UUIDField(models.UUIDField):
    """UUIDField with configurable version and sensible defaults."""

    def __init__(
        self,
        verbose_name: str | None = None,
        primary_key: bool = False,
        version: int = 4,
        editable: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
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
