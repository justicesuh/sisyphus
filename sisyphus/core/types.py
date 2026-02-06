from __future__ import annotations

from typing import TYPE_CHECKING

from django.http import HttpRequest

if TYPE_CHECKING:
    from django_htmx.middleware import HtmxDetails

    from sisyphus.accounts.models import User


class AuthedHttpRequest(HttpRequest):
    """HttpRequest with user narrowed to an authenticated User."""

    user: User


class HtmxHttpRequest(AuthedHttpRequest):
    """AuthedHttpRequest with the htmx attribute added by HtmxMiddleware."""

    htmx: HtmxDetails
