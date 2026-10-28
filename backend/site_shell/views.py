"""Serves the public site: the built React app (docs/architecture.md, section 8, Serving).

Django returns the same `index.html` for every public URL and React Router picks the page.
The JS and CSS it links to are static files, served by WhiteNoise.
Each page gets its own `<title>` and meta description (`site_shell.meta`).
"""

import re

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_cache_control
from django.utils.html import format_html
from django.views.decorators.http import require_safe

from site_shell.meta import NOT_FOUND, PageMeta, page_meta

MISSING_BUILD_MESSAGE = (
    "The frontend is not built. Run `npm run build` in frontend/, "
    "or use `make dev` and open the Vite server."
)
TITLE = re.compile(r"<title>.*?</title>", re.DOTALL)


def with_meta(html: str, meta: PageMeta) -> str:
    """`html` with its `<title>` replaced by the page's title and description."""
    tags = format_html(
        '<title>{title}</title><meta name="description" content="{description}" />'
        '<meta property="og:title" content="{title}" />'
        '<meta property="og:description" content="{description}" />',
        title=meta.title,
        description=meta.description,
    )
    return TITLE.sub(lambda _: tags, html, count=1)


@require_safe
def index(request: HttpRequest) -> HttpResponse:
    try:
        html = (settings.FRONTEND_DIST_DIR / "index.html").read_text(encoding="utf-8")
    except FileNotFoundError:
        return HttpResponse(
            MISSING_BUILD_MESSAGE, status=503, content_type="text/plain; charset=utf-8"
        )
    meta = page_meta(request)
    # A URL with no page still gets the app, which shows its "not found" page.
    response = HttpResponse(with_meta(html, meta or NOT_FOUND), status=200 if meta else 404)
    # Asset names carry a content hash, so only index.html must be revalidated after a deploy.
    patch_cache_control(response, no_cache=True)
    return response
