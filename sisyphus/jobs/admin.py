from django.contrib import admin
from django.utils.html import format_html

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.jobs.models import Company, Location, Job, Event


class CompanyAdmin(UUIDModelAdmin):
    list_display = ('name', 'href', 'banned')
    list_filter = ('banned',)
    search_fields = ('name',)

    def href(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.url,
            obj.url,
        )
    href.short_description = 'URL'


class LocationAdmin(UUIDModelAdmin):
    list_display = ('name', 'geo_id')
    search_fields = ('name',)


class JobAdmin(UUIDModelAdmin):
    list_display = ('title', 'href', 'populated', 'easy_apply', 'status')
    list_editable = ('status',)
    list_filter = ('populated', 'easy_apply', 'status')
    list_per_page = 25
    search_fields = ('company__name', 'title')

    def href(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.url,
            obj.url,
        )
    href.short_description = 'URL'


admin.site.register(Company, CompanyAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Event, UUIDModelAdmin)
