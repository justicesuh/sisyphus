from __future__ import annotations

from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

if TYPE_CHECKING:
    from collections.abc import Callable

    from django.http import HttpRequest, HttpResponse


class TimezoneMiddleware:
    """Activate the user's preferred timezone for each request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process the request and activate the user's timezone."""
        if request.user.is_authenticated:
            try:
                tzname = request.user.profile.timezone
                if tzname:
                    timezone.activate(ZoneInfo(tzname))
            except ZoneInfoNotFoundError, AttributeError, KeyError:
                timezone.deactivate()
        return self.get_response(request)
