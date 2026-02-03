from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.resumes.models import Resume


@admin.register(Resume)
class ResumeAdmin(UUIDModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'user__user__email')
