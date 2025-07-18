from django.contrib import admin

from sisyphus.core.admin import UUIDModelAdmin
from sisyphus.users.models import User

admin.site.register(User, UUIDModelAdmin)
