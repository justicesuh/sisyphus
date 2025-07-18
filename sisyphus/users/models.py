from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDMixin


class User(AbstractUser, UUIDMixin):
    email = models.EmailField(_('email address'), unique=True)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email
