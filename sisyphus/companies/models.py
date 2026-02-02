from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDModel


class Company(UUIDModel):
    name = models.CharField(max_length=255)
    website = models.URLField(unique=True, null=True, blank=True)
    linkedin_url = models.URLField(unique=True, null=True, blank=True)

    is_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self):
        return self.name

    def ban(self, reason: str = '') -> None:
        from sisyphus.jobs.models import Job
        self.is_banned = True
        self.banned_at = timezone.now()
        self.ban_reason = reason
        self.save(update_fields=['is_banned', 'banned_at', 'ban_reason'])
        jobs_to_ban = self.jobs.filter(status__in=[Job.Status.NEW, Job.Status.SAVED])
        for job in jobs_to_ban:
            job.pre_ban_status = job.status
            job.status = Job.Status.BANNED
            job.save(update_fields=['status', 'pre_ban_status'])

    def unban(self) -> None:
        from sisyphus.jobs.models import Job
        self.is_banned = False
        self.banned_at = None
        self.ban_reason = ''
        self.save(update_fields=['is_banned', 'banned_at', 'ban_reason'])
        for job in self.jobs.filter(status=Job.Status.BANNED):
            job.status = job.pre_ban_status or Job.Status.NEW
            job.pre_ban_status = None
            job.save(update_fields=['status', 'pre_ban_status'])
