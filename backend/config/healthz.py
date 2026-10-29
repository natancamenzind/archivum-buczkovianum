"""Liveness check for the deployment (US-OPS-01 AC6). A plain Django view, not part of the API."""

from django.db import DatabaseError, connection
from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_safe


@require_safe
def healthz(request: HttpRequest) -> HttpResponse:
    """Return 200 "ok" when the database answers ``SELECT 1``, 503 otherwise."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return HttpResponse("database unavailable", status=503, content_type="text/plain")
    return HttpResponse("ok", content_type="text/plain")
