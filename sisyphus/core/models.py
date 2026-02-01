from django.db import models

from sisyphus.core.fields import AutoCreatedField, AutoUpdatedField


class TimestampedMixin(models.Model):
    created_at = AutoCreatedField()
    updated_at = AutoUpdatedField()

    class Meta:
        abstract = True
