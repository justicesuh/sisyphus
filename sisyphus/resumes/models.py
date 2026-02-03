from django.db import models

from sisyphus.accounts.models import UserProfile
from sisyphus.core.models import UUIDModel


def resume_upload_path(instance, filename):
    return f'resumes/{instance.user.uuid}/{filename}'


class Resume(UUIDModel):
    user = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='resume',
    )
    name = models.CharField(max_length=255, help_text='A label for this resume (e.g., "Software Engineer Resume")')
    file = models.FileField(upload_to=resume_upload_path)
    text = models.TextField(blank=True, help_text='Extracted text content from the resume')

    def __str__(self):
        return self.name

    def extract_text(self):
        """Extract text from PDF file and save to text field."""
        if not self.file:
            return

        filename = self.file.name.lower()
        if not filename.endswith('.pdf'):
            return

        try:
            import fitz

            self.file.seek(0)
            pdf_bytes = self.file.read()
            doc = fitz.open(stream=pdf_bytes, filetype='pdf')

            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())

            doc.close()
            self.text = '\n'.join(text_parts).strip()
            self.save(update_fields=['text'])
        except Exception:
            pass
