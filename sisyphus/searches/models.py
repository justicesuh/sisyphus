from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Location


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
    def geo_id(self):
        geo_id = getattr(self.location, 'geo_id', None)
        if geo_id is None:
            return Location.WORLDWIDE
        return int(geo_id)


class SearchRun(UUIDModel):
    class Status(models.TextChoices):
        RUNNING = 'running', _('Running')
        SUCCESS = 'success', _('Success')
        ERROR = 'error', _('Error')

    search = models.ForeignKey(Search, related_name='runs', on_delete=models.CASCADE)
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
