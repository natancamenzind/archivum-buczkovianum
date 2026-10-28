from pathlib import Path

import pytest
from pytest_django.fixtures import Settings

SCRIPT = "assets/index-B2gSypW-.js"
INDEX_HTML = (
    '<!doctype html><html lang="pl"><head><meta charset="UTF-8" />'
    "<title>Archivum Buczkovianum</title>"
    f'<script type="module" crossorigin src="/static/{SCRIPT}"></script>'
    '</head><body><div id="root"></div></body></html>'
)


@pytest.fixture
def frontend_dist(settings: Settings, tmp_path: Path) -> Path:
    """A built frontend as Vite writes it: index.html and hashed assets under assets/."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (dist / SCRIPT).write_text("console.log('app')", encoding="utf-8")
    # Vite links fonts by absolute URL under the `/static/` base.
    (dist / "assets" / "index-D9RQlONl.css").write_text(
        "@font-face{src:url(/static/assets/lora-latin-400-normal-DnxXpLNu.woff2)}",
        encoding="utf-8",
    )
    (dist / "assets" / "lora-latin-400-normal-DnxXpLNu.woff2").write_bytes(b"font")
    settings.FRONTEND_DIST_DIR = dist
    settings.STATICFILES_DIRS = [dist]
    return dist
