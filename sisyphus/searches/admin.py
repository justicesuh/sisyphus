from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.searches.models import Source, Search, SearchRun

admin.site.register(Source, UUIDModelAdmin)
admin.site.register(Search, UUIDModelAdmin)
admin.site.register(SearchRun, UUIDModelAdmin)
