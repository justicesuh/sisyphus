from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDModel


class Company(UUIDModel):
    """A company that posts jobs."""

    name = models.CharField(max_length=255)
    website = models.URLField(unique=True, null=True, blank=True)
    linkedin_url = models.URLField(unique=True, null=True, blank=True)

    is_banned = models.BooleanField(default=False)
    banned_at = models.DateTimeField(null=True, blank=True)
    ban_reason = models.TextField(blank=True)

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')

    def __str__(self) -> str:
        """Return the company name."""
        return self.name

    def add_note(self, text: str) -> CompanyNote:
        """Add a note to this company."""
        return CompanyNote.objects.create(company=self, text=text)

    def ban(self, reason: str = '') -> None:
        """Ban this company and update associated jobs."""
        from sisyphus.jobs.models import Job  # noqa: PLC0415

        self.is_banned = True
        self.banned_at = timezone.now()
        self.ban_reason = reason
        self.save(update_fields=['is_banned', 'banned_at', 'ban_reason'])
        for job in self.jobs.filter(status__in=[Job.Status.NEW, Job.Status.SAVED]):
            job.update_status(Job.Status.BANNED)

    def unban(self) -> None:
        """Unban this company and restore associated jobs."""
        from sisyphus.jobs.models import Job  # noqa: PLC0415

        self.is_banned = False
        self.banned_at = None
        self.ban_reason = ''
        self.save(update_fields=['is_banned', 'banned_at', 'ban_reason'])
        for job in self.jobs.filter(status=Job.Status.BANNED):
            job.update_status(job.pre_ban_status or Job.Status.NEW)


class CompanyNote(UUIDModel):
    """A note attached to a company."""

    company = models.ForeignKey(Company, related_name='notes', on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)

    def __str__(self) -> str:
        """Return the company name and note text."""
        return f'{self.company.name} | {self.text}'
