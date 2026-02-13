from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.jobs.models import Job, Location

admin.site.register(Location, UUIDModelAdmin)


@admin.register(Job)
class JobAdmin(UUIDModelAdmin):
    list_display = ('title', 'user', 'company_link', 'status', 'date_posted_date')
    list_filter = ('user', 'status', 'flexibility')
    search_fields = ('title', 'company__name')
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description='company', ordering='company__name')
    def company_link(self, obj):
        url = reverse('admin:companies_company_change', args=[obj.company_id])
        return format_html('<a href="{}">{}</a>', url, obj.company)

    @admin.display(description='date posted', ordering='date_posted')
    def date_posted_date(self, obj):
        return obj.date_posted.date() if obj.date_posted else None
