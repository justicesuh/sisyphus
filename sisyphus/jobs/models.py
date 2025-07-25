from datetime import datetime

from django.db import models
from django.utils import timezone

from sisyphus.core.models import UUIDModel


class Company(UUIDModel):
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    banned = models.BooleanField(default=False)
    banned_reason = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'company'
        verbose_name_plural = 'companies'

    def ban(self, reason):
        self.banned = True
        self.banned_reason = reason
        self.save()

    def unban(self):
        self.banned = False
        self.banned_reason = None
        self.save()

    def __str__(self):
        return self.name


class Location(UUIDModel):
    name = models.CharField(max_length=255)
    geo_id = models.IntegerField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name


class JobManager(models.Manager):
    def add_job(self, job: dict, search) -> bool:
        company, _ = Company.objects.get_or_create(
            url=job['company_url'],
            defaults={
                'name': job['company'],
            }
        )
        if company.banned:
            return False

        location = None
        if job['location'] is not None:
            location, _ = Location.objects.get_or_create(
                name=job['location'],
            )

        _, created = self.get_or_create(
            url=job['url'],
            defaults={
                'company': company,
                'title': job['title'],
                'location': location,
                'date_posted': timezone.make_aware(datetime.strptime(job['date_posted'], '%Y-%m-%d')).date(),
                'date_found': timezone.make_aware(datetime.strptime(job['date_found'], '%Y-%m-%d')).date(),
                'search': search,
                'flexibility': search.flexibility,
            }
        )
        return created

    def add_jobs(self, jobs: list[dict], search) -> int:
        count = 0
        for job in jobs:
            created = self.add_job(job, search)
            if created:
                count += 1
        return count

    def banned(self):
        return self.filter(company__banned=True).exclude(status=Job.DISMISSED)

    def calculate_metric(self, title: str, width: int, color: str, status):
        if status is None:
            value = Job.objects.filter(status=Job.NEW).count()
        elif status is True:
            value = Job.objects.filter(status=Job.NEW, populated=True, easy_apply=True).count()
        elif status is False:
            value = Job.objects.filter(status=Job.NEW, populated=True, easy_apply=False).count()
        elif status == Job.APPLIED:
            value = Job.objects.filter(date_applied__isnull=False).count()
        else:
            value = Job.objects.filter(status=status).count()
        return {
            'title': title,
            'width': width,
            'color': color,
            'value': value,
        }

    def metrics(self):
        metrics = []
        statuses = [
            (None, 'dark'),
            (Job.SAVED, 'info'),
            (Job.DISMISSED, 'danger'),
            (True, 'primary'),
            (False, 'warning'),
            (Job.APPLIED, 'success'),
            (Job.INTERVIEW, 'info'),
        ]
        for status, color in statuses:
            if status is None:
                title = 'Available'
            elif status is True:
                title = 'Easy Apply'
            elif status is False:
                title = 'External'
            else:
                title = status.capitalize()
                if status == Job.OFFER:
                    title += 's'
                elif status == Job.INTERVIEW:
                    title += 'ing'
            if status is None or status == Job.SAVED or status == Job.DISMISSED:
                width = 4
            else:
                width = 3
            metrics.append(self.calculate_metric(title, width, color, status))
        return metrics

    def next_job(self, saved=False):
        status = Job.SAVED if saved else Job.NEW
        return self.filter(status=status, populated=True).order_by(
            '-easy_apply',
            '-date_posted',
        ).first()

    def field_contains(self, field, value):
        return self.filter(**{f'{field}__icontains': value}).exclude(status=Job.DISMISSED)


class Job(UUIDModel):
    HYBRID = 'hybrid'
    ONSITE = 'onsite'
    REMOTE = 'remote'

    NEW = 'new'
    SAVED = 'saved'
    DISMISSED = 'dismissed'
    EXPIRED = 'expired'
    APPLIED = 'applied'
    REJECTED = 'rejected'
    INTERVIEW = 'interview'
    OFFER = 'offer'
    ACCEPTED = 'accepted'
    WITHDRAWN = 'withdrawn'

    FLEXIBILITY_CHOICES = (
        (HYBRID, HYBRID.capitalize()),
        (ONSITE, ONSITE.capitalize()),
        (REMOTE, REMOTE.capitalize()),
    )

    STATUS_CHOICES = (
        (NEW, NEW.capitalize()),
        (SAVED, SAVED.capitalize()),
        (DISMISSED, DISMISSED.capitalize()),
        (EXPIRED, EXPIRED.capitalize()),
        (APPLIED, APPLIED.capitalize()),
        (REJECTED, REJECTED.capitalize()),
        (INTERVIEW, INTERVIEW.capitalize()),
        (OFFER, OFFER.capitalize()),
        (ACCEPTED, ACCEPTED.capitalize()),
        (WITHDRAWN, WITHDRAWN.capitalize()),
    )

    company = models.ForeignKey(Company, related_name='jobs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField(unique=True)
    location = models.ForeignKey(Location, related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    date_posted = models.DateField()

    search = models.ForeignKey('search.Search', related_name='jobs', on_delete=models.SET_NULL, null=True, blank=True)
    date_found = models.DateField()
    populated = models.BooleanField(default=False)

    easy_apply = models.BooleanField(default=False)
    flexibility = models.CharField(max_length=6, choices=FLEXIBILITY_CHOICES, default=ONSITE)
    description = models.TextField(null=True, blank=True)
    raw_html = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=9, choices=STATUS_CHOICES, default=NEW)
    date_applied = models.DateField(null=True, blank=True)

    objects = JobManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cached_status = self.status

    def update_status(self, new_status: str):
        if self.cached_status == new_status:
            return False
        self.status = new_status
        event = Event.objects.create(
            event_type=Event.STATUS,
            job=self,
            old_status=self.cached_status,
            new_status=self.status
        )
        event.save()
        self.cached_status = self.status

        if self.status == Job.APPLIED:
            self.date_applied = timezone.now().date()
        self.save()
        return True

    def add_note(self, note: str):
        event = Event.objects.create(event_type=Event.NOTE, job=self, note=note)
        event.save()
        self.save()

    def dismiss(self, reason):
        self.update_status(Job.DISMISSED)
        self.add_note(reason)

    def save(self, *args, **kwargs):
        self.update_status(self.status)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Event(UUIDModel):
    NOTE = 'note'
    STATUS = 'status'

    EVENT_TYPE_CHOICES = (
        (NOTE, NOTE.capitalize()),
        (STATUS, STATUS.capitalize()),
    )

    event_type = models.CharField(max_length=6, choices=EVENT_TYPE_CHOICES)
    job = models.ForeignKey(Job, related_name='_events', on_delete=models.CASCADE)

    old_status = models.CharField(max_length=10, null=True, blank=True)
    new_status = models.CharField(max_length=10, null=True, blank=True)

    note = models.TextField(null=True, blank=True)

    def __str__(self):
        ret = f'{self.job.title} | '
        if self.event_type == Event.NOTE:
            ret += self.note
        else:
            ret += f'{self.old_status} -> {self.new_status}'
        return ret
