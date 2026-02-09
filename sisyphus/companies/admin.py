from django.contrib import admin

from sisyphus.companies.models import Company
from sisyphus.core.admin import UUIDModelAdmin


@admin.register(Company)
class CompanyAdmin(UUIDModelAdmin):
    list_display = ('name', 'user', 'website', 'is_banned')
    list_filter = ('user', 'is_banned')
