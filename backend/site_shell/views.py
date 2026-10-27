"""Serves the public site: the built React app (docs/architecture.md, section 8, Serving).

Django returns the same `index.html` for every public URL and React Router picks the page.
The JS and CSS it links to are static files, served by WhiteNoise.
"""

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control
from django.views.decorators.http import require_safe

MISSING_BUILD_MESSAGE = (
    "The frontend is not built. Run `npm run build` in frontend/, "
    "or use `make dev` and open the Vite server."
)


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    try:
        html = (settings.FRONTEND_DIST_DIR / "index.html").read_text(encoding="utf-8")
    except FileNotFoundError:
        return HttpResponse(
            MISSING_BUILD_MESSAGE, status=503, content_type="text/plain; charset=utf-8"
        )
    response = HttpResponse(html)
    # Asset names carry a content hash, so only index.html must be revalidated after a deploy.
    patch_cache_control(response, no_cache=True)
    return response
