from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.jobs.models import Job, Location

admin.site.register(Location, UUIDModelAdmin)


@admin.register(Job)
class JobAdmin(UUIDModelAdmin):
    list_display = ('title', 'user', 'company', 'status', 'date_posted')
    list_filter = ('user', 'status', 'flexibility')
