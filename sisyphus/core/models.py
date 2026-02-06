from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.core.fields import AutoCreatedField, AutoUpdatedField, UUIDField


class TimestampedMixin(models.Model):
    """Abstract mixin providing created_at and updated_at timestamps."""

    created_at = AutoCreatedField()
    updated_at = AutoUpdatedField()

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    """Abstract mixin providing a UUID field."""

    uuid = UUIDField(_('UUID'))

    class Meta:
        abstract = True


class UUIDModel(TimestampedMixin, UUIDMixin):
    """Abstract base model with UUID and timestamp fields."""

    class Meta:
        abstract = True
