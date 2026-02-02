from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.jobs.models import Location, Job

admin.site.register(Location, UUIDModelAdmin)
admin.site.register(Job, UUIDModelAdmin)
