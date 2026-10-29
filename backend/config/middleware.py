"""Test-environment guards (US-OPS-01 AC3, AC4): basic auth and noindex, both off by default."""

import base64
import binascii
import secrets
from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse

# The one path Railway's healthcheck calls without credentials (US-OPS-01 AC6).
EXEMPT_PATHS = frozenset({"/healthz"})


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
        response = self.get_response(request)
        if settings.ROBOTS_NOINDEX:
            response["X-Robots-Tag"] = "noindex, nofollow"
        return response
