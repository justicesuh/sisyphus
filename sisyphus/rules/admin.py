from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.rules.models import Rule

admin.site.register(Rule, UUIDModelAdmin)
