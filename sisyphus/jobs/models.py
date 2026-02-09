import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from django.db import models
from django.utils import dateparse, timezone
from django.utils.translation import gettext_lazy as _

from sisyphus.accounts.models import UserProfile
from sisyphus.companies.models import Company
from sisyphus.core.models import UUIDModel

if TYPE_CHECKING:
    from celery.result import AsyncResult

    from sisyphus.resumes.models import Resume
    from sisyphus.searches.models import SearchRun

logger = logging.getLogger(__name__)


class Location(UUIDModel):
    """A geographic location for job listings."""

    WORLDWIDE = 92000000

    name = models.CharField(max_length=255, unique=True)
    geo_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self) -> str:
        """Return the location name."""
        return self.name


class JobManager(models.Manager):
    """Custom model manager for Job."""

    def parse_datetime(self, datetime_str: str) -> datetime | None:
        """Parse datetime string and make timezone aware."""
        dt = dateparse.parse_datetime(datetime_str)
        if dt is None:
            logger.warning('dateparse.parse_datetime failed for %s. Setting to None', datetime_str)
            return None
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return dt
    
    def add_job(self, job: dict, search_run: 'SearchRun') -> bool:
        """Add parsed job to database."""
        user = search_run.search.user
        company, _ = Company.objects.get_or_create(linkedin_url=job['company_url'], user=user, defaults={'name': job['company']})

        location = None
        if job['location'] is not None:
            location, _  = Location.objects.get_or_create(name=job['location'])

        _, created = self.get_or_create(
            url=job['url'],
            user=user,
            defaults={
                'company': company,
                'title': job['title'],
                'location': location,
                'date_posted': self.parse_datetime(job['date_posted']),
                'search_run': search_run,
                'date_found': self.parse_datetime(job['date_found']),
                'flexibility': search_run.search.flexibility,
            }
        )
        return created
    
    def add_jobs(self, jobs: list[dict], search_run: 'SearchRun') -> int:
        return sum(1 for job in jobs if self.add_job(job, search_run))


class Job(UUIDModel):
    """A job listing tracked in the system."""

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

    user = models.ForeignKey(UserProfile, related_name='jobs', on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name='jobs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField()
    location = models.ForeignKey(Location, related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    date_posted = models.DateTimeField(null=True, blank=True)

    search_run = models.ForeignKey('searches.SearchRun', related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    date_found = models.DateTimeField(null=True, blank=True)
    populated = models.BooleanField(default=False)

    flexibility = models.CharField(max_length=6, choices=Flexibility.choices, default='', blank=True)

    raw_html = models.TextField(default='', blank=True)
    description = models.TextField(default='', blank=True)
    easy_apply = models.BooleanField(default=False)

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    pre_ban_status = models.CharField(max_length=12, choices=Status.choices, default='', blank=True)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    score = models.IntegerField(null=True, blank=True)
    score_explanation = models.TextField(default='', blank=True)
    score_task_id = models.CharField(max_length=255, blank=True)

    objects = JobManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['url', 'user'], name='unique_job_url_per_user'),
        ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the job and cache the current status."""
        super().__init__(*args, **kwargs)
        self.cached_status = self.status

    def __str__(self) -> str:
        """Return the job title."""
        return self.title

    def add_note(self, text: str) -> JobNote:
        """Create a note for this job."""
        return JobNote.objects.create(job=self, text=text)

    def calculate_score(self, resume: Resume) -> AsyncResult | None:
        """Queue a Celery task to calculate the job-resume fit score."""
        if self.score is not None:
            return None

        if not self.populated:
            return None

        from celery.result import AsyncResult as _AsyncResult  # noqa: PLC0415
        from django.db import transaction  # noqa: PLC0415

        from sisyphus.jobs.tasks import calculate_job_score  # noqa: PLC0415

        with transaction.atomic():
            job = Job.objects.select_for_update().get(id=self.id)

            if job.score is not None:
                return None

            if job.score_task_id:
                result = _AsyncResult(job.score_task_id)
                if not result.ready():
                    return None

            result = calculate_job_score.delay(self.id, resume.id)
            job.score_task_id = result.id
            job.save(update_fields=['score_task_id'])

        self.score_task_id = result.id
        return result

    def update_status(self, new_status: str) -> None:
        """Update the job status and record a status change event."""
        if self.cached_status == new_status:
            return

        update_fields = ['status', 'date_status_changed']

        if new_status == self.Status.BANNED:
            self.pre_ban_status = self.cached_status
            update_fields.append('pre_ban_status')
        elif self.cached_status == self.Status.BANNED:
            self.pre_ban_status = ''
            update_fields.append('pre_ban_status')

        self.status = new_status
        event = JobEvent.objects.create(job=self, old_status=self.cached_status, new_status=self.status)
        self.cached_status = self.status
        self.date_status_changed = event.created_at
        self.save(update_fields=update_fields)


class JobEvent(UUIDModel):
    """A record of a job status change."""

    job = models.ForeignKey(Job, related_name='events', on_delete=models.CASCADE)
    old_status = models.CharField(max_length=12, choices=Job.Status.choices)
    new_status = models.CharField(max_length=12, choices=Job.Status.choices)

    def __str__(self) -> str:
        """Return a summary of the status change."""
        return f'{self.job.title} | {self.get_old_status_display()} -> {self.get_new_status_display()}'


class JobNote(UUIDModel):
    """A user note attached to a job."""

    job = models.ForeignKey(Job, related_name='notes', on_delete=models.CASCADE)
    text = models.TextField(default='', blank=True)

    def __str__(self) -> str:
        """Return a summary of the note."""
        return f'{self.job.title} | {self.text}'
