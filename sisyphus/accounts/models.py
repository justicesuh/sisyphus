import zoneinfo
from typing import Any, ClassVar

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from sisyphus.core.models import UUIDMixin


def get_timezone_choices() -> list[tuple[str, str]]:
    """Return a list of timezone choices."""
    return [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]


class UserManager(BaseUserManager):
    """Manager for custom User model."""

    use_in_migrations: ClassVar[bool] = True

    def _create_user(self, email: str, password: str, **extra_fields: Any) -> User:
        if not email:
            raise ValueError('The email field must be set.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str, **extra_fields: Any) -> User:
        """Create and return a regular user."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> User:
        """Create and return a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDMixin):
    """Custom user model using email as the unique identifier."""

    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Enter a valid email address.'),
        error_messages={
            'unique': _('A user with that email address already exists.'),
        },
    )
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this user should be active. Unselect this instead of deleting accounts.'),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD: ClassVar[str] = 'email'
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self) -> None:
        """Normalize the email address."""
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self) -> str:
        """Return the full name of the user."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self) -> str:
        """Return the first name of the user."""
        return self.first_name

    def email_user(self, subject: str, message: str, from_email: str | None = None, **kwargs: Any) -> None:
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)


class UserProfile(UUIDMixin):
    """Profile extending the User model with additional preferences."""

    user = models.OneToOneField(User, related_name='profile', on_delete=models.CASCADE)
    timezone = models.CharField(max_length=50, choices=get_timezone_choices, default='UTC', verbose_name='Timezone')

    def __str__(self) -> str:
        """Return the user's email."""
        return self.user.email
