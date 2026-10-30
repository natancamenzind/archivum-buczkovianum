"""Deployment middleware: the health check (US-OPS-01 AC6) and the test-environment guards
(AC3, AC4), basic auth and noindex, both off by default."""

import base64
import binascii
import secrets
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from config.healthz import healthz

HEALTHZ_PATH = "/healthz"
# The one path the platform's health check calls without credentials (US-OPS-01 AC6).
EXEMPT_PATHS = frozenset({HEALTHZ_PATH})


def add_noindex(response: HttpResponse) -> HttpResponse:
    """Add X-Robots-Tag when ROBOTS_NOINDEX is on (US-OPS-01 AC4)."""
    if settings.ROBOTS_NOINDEX:
        response["X-Robots-Tag"] = "noindex, nofollow"
    return response


class HealthzMiddleware:
    """Answer /healthz itself, first in MIDDLEWARE, before anything validates the Host header.

    Platform health checks may call the container by its internal address rather than the
    public host, which is not in ALLOWED_HOSTS. Nothing here reads the host.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path_info != HEALTHZ_PATH:
            return self.get_response(request)
        return add_noindex(healthz(request))


class BasicAuthMiddleware:
    """Require the credentials in BASIC_AUTH_USER and BASIC_AUTH_PASSWORD when both are set."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user, password = settings.BASIC_AUTH_USER, settings.BASIC_AUTH_PASSWORD
        if not (user and password) or request.path in EXEMPT_PATHS:
            return self.get_response(request)
        if self._authorized(request.headers.get("Authorization", ""), user, password):
            return self.get_response(request)
        response = HttpResponse("Authentication required", status=401, content_type="text/plain")
        response["WWW-Authenticate"] = 'Basic realm="Archivum Buczkovianum", charset="UTF-8"'
        return response

    @staticmethod
    def _authorized(header: str, user: str, password: str) -> bool:
        scheme, _, encoded = header.partition(" ")
        if scheme.lower() != "basic":
            return False
        try:
            decoded = base64.b64decode(encoded.strip(), validate=True)
        except binascii.Error:
            return False
        given_user, _, given_password = decoded.partition(b":")
        # Both compared every time, so the response time does not reveal which one was wrong.
        user_ok = secrets.compare_digest(given_user, user.encode())
        password_ok = secrets.compare_digest(given_password, password.encode())
        return user_ok and password_ok


class NoindexMiddleware:
    """Add X-Robots-Tag to every response when ROBOTS_NOINDEX is on."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return add_noindex(self.get_response(request))
