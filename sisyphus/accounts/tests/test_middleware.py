from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from django.utils import timezone

from sisyphus.accounts.middleware import TimezoneMiddleware


class TestTimezoneMiddleware:
    """Tests for the TimezoneMiddleware."""

    def test_authenticated_user_activates_timezone(self, user, user_profile):
        user_profile.timezone = 'US/Eastern'
        user_profile.save()

        request = MagicMock()
        request.user = user

        get_response = MagicMock(return_value=MagicMock())
        middleware = TimezoneMiddleware(get_response)
        middleware(request)

        assert timezone.get_current_timezone() == ZoneInfo('US/Eastern')
        timezone.deactivate()

    def test_unauthenticated_user_no_activation(self):
        request = MagicMock()
        request.user.is_authenticated = False

        get_response = MagicMock(return_value=MagicMock())
        middleware = TimezoneMiddleware(get_response)
        middleware(request)

        get_response.assert_called_once_with(request)
