from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.jobs.models import Company, Location, Job

admin.site.register(Company, UUIDModelAdmin)
admin.site.register(Location, UUIDModelAdmin)
admin.site.register(Job, UUIDModelAdmin)
