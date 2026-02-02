from django.contrib import admin

from sisyphus.accounts.models import User
from sisyphus.core.admin import UUIDModelAdmin

admin.site.register(User, UUIDModelAdmin)
