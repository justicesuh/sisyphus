from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.search.models import Search

admin.site.register(Search, UUIDModelAdmin)
