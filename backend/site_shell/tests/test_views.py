from pathlib import Path

import pytest
from django.core.management import call_command
from django.http import StreamingHttpResponse
from django.test import Client
from pytest_django.fixtures import Settings

from site_shell.views import MISSING_BUILD_MESSAGE

INDEX_HTML = '<!doctype html><html lang="pl"><script src="/static/assets/app.js"></script></html>'


@pytest.fixture
def frontend_dist(settings: Settings, tmp_path: Path) -> Path:
    """A built frontend as Vite writes it: index.html and hashed assets under assets/."""
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (dist / "assets" / "app.js").write_text("console.log('app')", encoding="utf-8")
    # Vite links fonts by absolute URL under the `/static/` base.
    (dist / "assets" / "app.css").write_text(
        "@font-face{src:url(/static/assets/lora.woff2)}", encoding="utf-8"
    )
    (dist / "assets" / "lora.woff2").write_bytes(b"font")
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


@pytest.mark.parametrize("url", ["/static/missing.js", "/media/missing.pdf"])
def test_missing_files_are_404_not_the_index(client: Client, frontend_dist: Path, url: str) -> None:
    assert client.get(url).status_code == 404


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
    settings: Settings, frontend_dist: Path
) -> None:
    # The production storage hashes names and rewrites the CSS font URL; Vite's names must survive.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    call_command("collectstatic", interactive=False, verbosity=0)
    client = Client()  # A new client builds a new WhiteNoise middleware, which scans STATIC_ROOT.

    script = client.get("/static/assets/app.js")
    font = client.get("/static/assets/lora.woff2")

    assert script.status_code == 200
    assert isinstance(script, StreamingHttpResponse)
    assert script.getvalue() == b"console.log('app')"
    assert font.status_code == 200
