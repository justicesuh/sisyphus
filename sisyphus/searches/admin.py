from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.searches.models import Source, Search, SearchRun

admin.site.register(Source, UUIDModelAdmin)
admin.site.register(SearchRun, UUIDModelAdmin)


@admin.register(Search)
class SearchAdmin(UUIDModelAdmin):
    list_display = ('keywords', 'user', 'source', 'is_active', 'status', 'last_executed_at')
    list_filter = ('user', 'source', 'is_active', 'status')
