from __future__ import annotations

import logging

from django.db import models

from sisyphus.accounts.models import UserProfile
from sisyphus.core.models import UUIDModel

logger = logging.getLogger(__name__)


def resume_upload_path(instance: Resume, filename: str) -> str:
    """Return the upload path for a resume file."""
    return f'resumes/{instance.user.uuid}/{filename}'


class Resume(UUIDModel):
    """A user's uploaded resume document."""

    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='resume',
    )
    name = models.CharField(max_length=255, help_text='A label for this resume (e.g., "Software Engineer Resume")')
    file = models.FileField(upload_to=resume_upload_path)
    text = models.TextField(blank=True, help_text='Extracted text content from the resume')

    def __str__(self) -> str:
        """Return the resume name."""
        return self.name

    def extract_text(self) -> None:
        """Extract text from PDF file and save to text field."""
        if not self.file:
            return

        filename = self.file.name.lower()
        if not filename.endswith('.pdf'):
            return

        try:
            import fitz  # noqa: PLC0415

            self.file.seek(0)
            pdf_bytes = self.file.read()
            doc = fitz.open(stream=pdf_bytes, filetype='pdf')

            text_parts = [page.get_text() for page in doc]

            doc.close()
            self.text = '\n'.join(text_parts).strip()
            self.save(update_fields=['text'])
        except ImportError, OSError, ValueError:
            logger.exception('Failed to extract text from resume %s', self.pk)
