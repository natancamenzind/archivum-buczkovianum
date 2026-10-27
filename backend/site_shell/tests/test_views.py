import re
from pathlib import Path

import pytest
from django.core.management import call_command
from django.http import StreamingHttpResponse
from django.test import Client
from pytest_django.fixtures import Settings

from site_shell.views import MISSING_BUILD_MESSAGE

SCRIPT = "assets/index-B2gSypW-.js"
INDEX_HTML = f'<!doctype html><html lang="pl"><script src="/static/{SCRIPT}"></script></html>'


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


@pytest.mark.parametrize("url", ["/", "/works/wertepy", "/tags/dezerter/", "/search?q=dezerter"])
def test_public_urls_get_the_frontend_index(client: Client, frontend_dist: Path, url: str) -> None:
    response = client.get(url)

    assert response.status_code == 200
    assert response.content.decode() == INDEX_HTML
    assert response["Content-Type"] == "text/html; charset=utf-8"
    assert "no-cache" in response["Cache-Control"]


@pytest.mark.parametrize("url", ["/apiary", "/administration", "/statics/x", "/mediathek"])
def test_paths_that_only_start_like_django_prefixes_are_pages(
    client: Client, frontend_dist: Path, url: str
) -> None:
    assert client.get(url).status_code == 200


def test_api_urls_are_not_served_the_index(client: Client, frontend_dist: Path) -> None:
    assert client.get("/api/schema/").content != INDEX_HTML.encode()
    assert client.get("/api/unknown/").status_code == 404


@pytest.mark.django_db
def test_admin_urls_are_not_served_the_index(client: Client, frontend_dist: Path) -> None:
    response = client.get("/admin/login/")

    assert response.status_code == 200
    assert response.content != INDEX_HTML.encode()


def test_django_prefixes_without_slash_are_not_pages(client: Client, frontend_dist: Path) -> None:
    redirect = client.get("/admin")

    assert redirect.status_code == 301
    assert redirect["Location"] == "/admin/"
    assert client.get("/api").status_code == 404


@pytest.mark.parametrize(
    "url",
    [
        "/static/missing.js",
        "/media/missing.pdf",
        "/favicon.ico",
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap.xml/",
    ],
)
def test_missing_files_are_404_not_the_index(client: Client, frontend_dist: Path, url: str) -> None:
    assert client.get(url).status_code == 404


def test_local_media_files_are_served(
    client: Client, settings: Settings, tmp_path: Path, frontend_dist: Path
) -> None:
    settings.MEDIA_ROOT = tmp_path
    works = tmp_path / "works"
    works.mkdir()
    (works / "cover.png").write_bytes(b"png")

    response = client.get("/media/works/cover.png")

    assert response.status_code == 200
    assert isinstance(response, StreamingHttpResponse)
    assert response.getvalue() == b"png"


def test_pages_accept_head_but_not_post(client: Client, frontend_dist: Path) -> None:
    assert client.head("/works").status_code == 200
    assert client.post("/works").status_code == 405


def test_missing_build_is_a_clear_503(client: Client, settings: Settings, tmp_path: Path) -> None:
    settings.FRONTEND_DIST_DIR = tmp_path / "not-built"

    response = client.get("/works")

    assert response.status_code == 503
    assert response.content.decode() == MISSING_BUILD_MESSAGE
    assert response["Content-Type"] == "text/plain; charset=utf-8"


def test_built_assets_are_served_by_whitenoise_after_collectstatic(
    settings: Settings, frontend_dist: Path, tmp_path: Path
) -> None:
    # The production storage hashes names and rewrites the CSS font URL; Vite's names must survive.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    call_command("collectstatic", interactive=False, verbosity=0)
    client = Client()  # A new client builds a new WhiteNoise middleware, which scans STATIC_ROOT.

    script = client.get(f"/static/{SCRIPT}")
    font = client.get("/static/assets/lora-latin-400-normal-DnxXpLNu.woff2")

    # The autouse `_static_root` fixture (backend/conftest.py) keeps collectstatic in tmp_path.
    assert Path(settings.STATIC_ROOT).is_relative_to(tmp_path)
    assert (Path(settings.STATIC_ROOT) / SCRIPT).is_file()
    assert script.status_code == 200
    assert isinstance(script, StreamingHttpResponse)
    assert script.getvalue() == b"console.log('app')"
    assert "immutable" in script["Cache-Control"]
    assert font.status_code == 200
    assert "immutable" in font["Cache-Control"]
    assert "immutable" not in client.get("/static/index.html")["Cache-Control"]


@pytest.mark.parametrize(
    ("url", "immutable"),
    [
        ("/static/assets/index-B2gSypW-.js", True),
        ("/static/assets/lora-latin-ext-500-normal-BM33EBQZ.woff", True),
        ("/static/admin/css/base.6b1c3d0e4f5a.css", True),
        ("/static/assets/index-B2gSypW-.0123456789ab.js", True),
        ("/static/index.html", False),
        ("/static/admin/css/base.css", False),
        ("/static/admin/img/icon-viewlink.svg", False),
    ],
)
def test_only_content_hashed_static_files_are_immutable(
    settings: Settings, url: str, immutable: bool
) -> None:
    assert bool(re.search(settings.WHITENOISE_IMMUTABLE_FILE_TEST, url)) is immutable
