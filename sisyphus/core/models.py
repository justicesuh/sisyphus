from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.core.fields import AutoCreatedField, AutoUpdatedField, UUIDField


class TimestampedMixin(models.Model):
    created_at = AutoCreatedField()
    updated_at = AutoUpdatedField()

    class Meta:
        abstract = True


class UUIDMixin(models.Model):
    uuid = UUIDField(_('UUID'))

    class Meta:
        abstract = True


class UUIDModel(TimestampedMixin, UUIDMixin):
    class Meta:
        abstract = True
