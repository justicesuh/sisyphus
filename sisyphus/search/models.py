from django.db import models
from django.utils import timezone

from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Location, Job


class Search(UUIDModel):
    MONTH = 2592000
    WEEK = 604800
    DAY = 86400
    HOUR = 3600
    QUARTER_HOUR = 900

    PERIOD_CHOICES = (
        (MONTH, 'Monthly'),
        (WEEK, 'Weekly'),
        (DAY, 'Daily'),
        (HOUR, 'Hourly'),
        (QUARTER_HOUR, 'Quarter Hourly')
    )

    keywords = models.CharField(max_length=255)
    location = models.ForeignKey(Location, related_name='searches', on_delete=models.SET_NULL, null=True, blank=True)

    easy_apply = models.BooleanField(default=False)
    flexibility = models.CharField(max_length=6, choices=Job.FLEXIBILITY_CHOICES, default=Job.ONSITE)
    period = models.IntegerField(choices=PERIOD_CHOICES, default=WEEK)

    last_executed = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'search'
        verbose_name_plural = 'searches'

    @property
    def geo_id(self):
        if self.location is not None and self.location.geo_id is not None:
            return self.location.geo_id
        return 92000000

    def update_last_executed(self):
        self.last_executed = timezone.now()
        self.save()
