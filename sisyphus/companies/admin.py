from django.contrib import admin

from sisyphus.companies.models import Company
from sisyphus.core.admin import UUIDModelAdmin

admin.site.register(Company, UUIDModelAdmin)
