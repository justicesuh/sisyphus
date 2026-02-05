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
        BANNED = 'banned', _('Banned')
        SAVED = 'saved', _('Saved')
        EXPIRED = 'expired', _('Expired')
        APPLIED = 'applied', _('Applied')
        DISMISSED = 'dismissed', _('Dismissed')
        INTERVIEWING = 'interviewing', _('Interviewing')
        OFFER = 'offer', _('Offer')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
        GHOSTED = 'ghosted', _('Ghosted')
        ACCEPTED = 'accepted', _('Accepted')

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

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    pre_ban_status = models.CharField(max_length=12, choices=Status.choices, null=True, blank=True)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(null=True, blank=True)
    score_explanation = models.TextField(default='', blank=True)
    score_task_id = models.CharField(max_length=255, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_status = self.status

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.status == self.Status.APPLIED:
            from sisyphus.applications.models import Application
            Application.objects.get_or_create(job=self)

    def add_note(self, text):
        return JobNote.objects.create(job=self, text=text)

    def calculate_score(self, resume):
        if self.score is not None:
            return None

        if not self.populated:
            return None

        from celery.result import AsyncResult
        from django.db import transaction
        from sisyphus.jobs.tasks import calculate_job_score

        with transaction.atomic():
            job = Job.objects.select_for_update().get(id=self.id)

            if job.score is not None:
                return None

            if job.score_task_id:
                result = AsyncResult(job.score_task_id)
                if not result.ready():
                    return None

            result = calculate_job_score.delay(self.id, resume.id)
            job.score_task_id = result.id
            job.save(update_fields=['score_task_id'])

        self.score_task_id = result.id
        return result

    def update_status(self, new_status):
        if self.cached_status == new_status:
            return

        update_fields = ['status', 'date_status_changed']

        if new_status == self.Status.BANNED:
            self.pre_ban_status = self.cached_status
            update_fields.append('pre_ban_status')
        elif self.cached_status == self.Status.BANNED:
            self.pre_ban_status = None
            update_fields.append('pre_ban_status')

        self.status = new_status
        event = JobEvent.objects.create(job=self, old_status=self.cached_status, new_status=self.status)
        self.cached_status = self.status
        self.date_status_changed = event.created_at
        self.save(update_fields=update_fields)


class JobEvent(UUIDModel):
    job = models.ForeignKey(Job, related_name='events', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=12, choices=Job.Status.choices)
    new_status = models.CharField(max_length=12, choices=Job.Status.choices)

    def __str__(self):
        return f'{self.job.title} | {self.get_old_status_display()} -> {self.get_new_status_display()}'


class JobNote(UUIDModel):
    job = models.ForeignKey(Job, related_name='notes', on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)

    def __str__(self):
        return f'{self.job.title} | {self.text}'
