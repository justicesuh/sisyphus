from django.db import models

from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Job


class Rule(UUIDModel):
    CONTAINS = 'contains'

    OPERATOR_CHOICES = (
        (CONTAINS, CONTAINS.capitalize()),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    field = models.CharField(max_length=255)
    operator = models.CharField(max_length=8, choices=OPERATOR_CHOICES, default=CONTAINS)
    value = models.CharField(max_length=255)
    status = models.CharField(max_length=9, choices=Job.STATUS_CHOICES, default=Job.NEW)

    def __str__(self):
        return self.name
