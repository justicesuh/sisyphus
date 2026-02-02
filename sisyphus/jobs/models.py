from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.companies.models import Company
from sisyphus.core.models import UUIDModel


class Location(UUIDModel):
    name = models.CharField(max_length=255, unique=True)
    geo_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Job(UUIDModel):
    class Status(models.TextChoices):
        NEW = 'new', _('New')
        FILTERED = 'filtered', _('Filtered')
        SAVED = 'saved', _('Saved')
        EXPIRED = 'expired', _('Expired')
        APPLIED = 'applied', _('Applied')
        DISMISSED = 'dismissed', _('Dismissed')

    class Flexibility(models.TextChoices):
        HYBRID = 'hybrid', _('Hybrid')
        ONSITE = 'onsite', _('Onsite')
        REMOTE = 'remote', _('Remote')

    company = models.ForeignKey(Company, related_name='jobs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    location = models.ForeignKey(Location, related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    date_posted = models.DateTimeField(null=True, blank=True)

    date_found = models.DateTimeField(null=True, blank=True)
    populated = models.BooleanField(default=False)

    flexibility = models.CharField(max_length=6, choices=Flexibility.choices, default=None, null=True, blank=True)

    raw_html = models.TextField(blank=True)
    description = models.TextField(blank=True)
    easy_apply = models.BooleanField(default=False)

    status = models.CharField(max_length=9, choices=Status.choices, default=Status.NEW)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
    

