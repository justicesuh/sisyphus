from zoneinfo import ZoneInfo

from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                tzname = request.user.profile.timezone
                if tzname:
                    timezone.activate(ZoneInfo(tzname))
            except Exception:
                timezone.deactivate()
        response = self.get_response(request)
        return response
