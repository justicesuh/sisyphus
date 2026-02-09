from enum import IntEnum

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Location, Job


class Period(IntEnum):
    """Represent common search periods."""

    MONTH = 2592000
    WEEK = 604800
    DAY = 86400
    HOUR = 3600


class Source(UUIDModel):
    name = models.CharField(max_length=32, unique=True)
    parser = models.CharField(max_length=32, unique=True)

    def __str__(self):
        return self.name


class Search(UUIDModel):
    class Status(models.TextChoices):
        IDLE = 'idle', _('Idle')
        QUEUED = 'queued', _('Queued')
        RUNNING = 'running', _('Running')
        SUCCESS = 'success', _('Success')
        ERROR = 'error', _('Error')

    keywords = models.CharField(max_length=255)
    location = models.ForeignKey(Location, related_name='searches', on_delete=models.SET_NULL, null=True, blank=True)

    easy_apply = models.BooleanField(default=False)
    is_hybrid = models.BooleanField(default=False)
    is_onsite = models.BooleanField(default=True)
    is_remote = models.BooleanField(default=False)

    source = models.ForeignKey(Source, related_name='searches', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    last_executed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.IDLE)

    class Meta:
        verbose_name = 'search'
        verbose_name_plural = 'searches'

    def __str__(self):
        return self.keywords
    
    @property
    def flexibility(self) -> str | None:
        """Compute job flexibility based on Search booleans.
        
        Return None if multiple booleans are True.
        """
        if sum(self.is_hybrid, self.is_onsite, self.is_remote) != 1:
            return None
        if self.is_hybrid:
            return Job.Flexibility.HYBRID
        if self.is_onsite:
            return Job.Flexibility.ONSITE
        if self.is_remote:
            return Job.Flexibility.REMOTE
        return None

    @property
    def geo_id(self):
        geo_id = getattr(self.location, 'geo_id', None)
        if geo_id is None:
            return Location.WORLDWIDE
        return int(geo_id)

    def calculate_period(self) -> int:
        """Return the multiple of a Period value closest to the time elapsed."""
        if not self.last_executed_at:
            return Period.MONTH

        delta = (timezone.now() - self.last_executed_at).total_seconds()

        best = Period.MONTH
        best_error = float('inf')
        for period in Period:
            multiple = max(1, round(delta / period))
            value = multiple * period
            error = abs(delta - value)
            if error < best_error:
                best = value
                best_error = error

        return best

    def set_status(self, status: Status) -> None:
        """Set status and save."""
        self.status = status
        update_fields = ['status']
        if self.status in [Search.Status.SUCCESS, Search.Status.ERROR]:
            self.last_executed_at = timezone.now()
            update_fields.append('last_executed_at')
        self.save(update_fields=update_fields)


class SearchRun(UUIDModel):
    class Status(models.TextChoices):
        RUNNING = 'running', _('Running')
        SUCCESS = 'success', _('Success')
        ERROR = 'error', _('Error')

    search = models.ForeignKey(Search, related_name='runs', on_delete=models.CASCADE)
    period = models.IntegerField(default=0)
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.RUNNING)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    jobs_found = models.PositiveIntegerField(default=0)
    jobs_created = models.PositiveIntegerField(default=0)

    error_message = models.TextField(default='', blank=True)

    class Meta:
        ordering = ('-started_at',)

    def __str__(self):
        return f'{self.search.keywords} | {self.get_status_display()} | {self.started_at}'
