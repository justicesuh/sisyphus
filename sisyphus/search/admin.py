from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.search.models import Search


class SearchAdmin(UUIDModelAdmin):
    list_display = ('__str__', 'location', 'flexibility', 'period', 'easy_apply', 'last_executed')
    list_filter = ('is_active',)


admin.site.register(Search, SearchAdmin)
