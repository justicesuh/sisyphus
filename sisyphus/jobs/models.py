from django.db import models

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


class Job(UUIDModel):
    HYBRID = 'hybrid'
    ONSITE = 'onsite'
    REMOTE = 'remote'

    INTERESTED = 'interested'
    DISMISSED = 'dismissed'
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
        (INTERESTED, INTERESTED.capitalize()),
        (DISMISSED, DISMISSED.capitalize()),
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

    date_found = models.DateField()
    populated = models.BooleanField(default=False)

    easy_apply = models.BooleanField(default=False)
    flexibility = models.CharField(max_length=6, choices=FLEXIBILITY_CHOICES, default=ONSITE)
    description = models.TextField(null=True, blank=True)
    raw_html = models.TextField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=INTERESTED)
    date_applied = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title
