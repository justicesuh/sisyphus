from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDModel
from sisyphus.jobs.models import Job


class Application(UUIDModel):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', _('Submitted')
        SCREENING = 'screening', _('Screening')
        INTERVIEWING = 'interviewing', _('Interviewing')
        OFFER = 'offer', _('Offer')
        REJECTED = 'rejected', _('Rejected')
        WITHDRAWN = 'withdrawn', _('Withdrawn')
        GHOSTED = 'ghosted', _('Ghosted')
        ACCEPTED = 'accepted', _('Accepted')

    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.SUBMITTED)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_status = self.status

    def __str__(self):
        return self.job.title
    
    def add_note(self, text):
        return ApplicationNote.objects.create(application=self, text=text)
    
    def update_status(self, new_status):
        if self.cached_status == new_status:
            return
        self.status = new_status
        event = ApplicationEvent.objects.create(application=self, old_status=self.cached_status, new_status=self.status)
        self.cached_status = self.status
        self.date_status_changed = event.created_at
        self.save(update_fields=['status', 'date_status_changed'])


class ApplicationEvent(UUIDModel):
    application = models.ForeignKey(Application, related_name='events', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=12, choices=Application.Status.choices)
    new_status = models.CharField(max_length=12, choices=Application.Status.choices)

    def __str__(self):
        return f'{str(self.application)} | {self.get_old_status_display()} -> {self.get_new_status_display()}'


class ApplicationNote(UUIDModel):
    application = models.ForeignKey(Application, related_name='notes', on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)

    def __str__(self):
        return f'{str(self.application)} | {self.text}'
