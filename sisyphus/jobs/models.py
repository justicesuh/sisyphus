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

    raw_html = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    easy_apply = models.BooleanField(default=False)

    status = models.CharField(max_length=9, choices=Status.choices, default=Status.NEW)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_status = self.status

    def __str__(self):
        return self.title
    
    def add_note(self, text):
        return JobNote.objects.create(job=self, text=text)

    def update_status(self, new_status):
        if self.cached_status == new_status:
            return
        self.status = new_status
        event = JobEvent.objects.create(job=self, old_status=self.cached_status, new_status=self.status)
        self.cached_status = self.status
        self.date_status_changed = event.created_at
        self.save(update_fields=['status', 'date_status_chaged'])


class JobEvent(UUIDModel):
    job = models.ForeignKey(Job, related_name='events', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=9, choices=Job.Status.choices)
    new_status = models.CharField(max_length=9, choices=Job.Status.choices)

    def __str__(self):
        return f'{self.job.title} | {self.get_old_status_display()} -> {self.get_new_status_display()}'


class JobNote(UUIDModel):
    job = models.ForeignKey(Job, related_name='notes', on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)

    def __str__(self):
        return f'{self.job.title} | {self.text}'
