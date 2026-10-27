"""Serve uploaded files from the local filesystem when S3 is not configured."""

from django.conf import settings
from django.http import HttpRequest, HttpResponseBase
from django.views.static import serve


def serve_local_media(request: HttpRequest, path: str) -> HttpResponseBase:
    """Expose MEDIA_ROOT under MEDIA_URL in development and other non-S3 deployments."""
    return serve(request, path, document_root=str(settings.MEDIA_ROOT))
