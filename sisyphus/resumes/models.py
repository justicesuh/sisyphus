from django.conf import settings
from django.db import models

from sisyphus.accounts.models import UserProfile
from sisyphus.core.models import UUIDModel


def resume_upload_path(instance, filename):
    return f'resumes/{instance.user.uuid}/{filename}'


class Resume(UUIDModel):
    user = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='resumes',
    )
    name = models.CharField(max_length=255, help_text='A label for this resume (e.g., "Software Engineer Resume")')
    file = models.FileField(upload_to=resume_upload_path)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
