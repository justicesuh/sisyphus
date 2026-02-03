from django.contrib import admin

from sisyphus.resumes.models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'user__email']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
