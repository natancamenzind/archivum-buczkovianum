import importlib
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import storages
from pytest_django.fixtures import Settings

from config import settings as settings_module


@pytest.fixture
def reload_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[ModuleType]:
    yield settings_module
    monkeypatch.undo()
    importlib.reload(settings_module)


def test_s3_region_and_endpoint_come_from_env(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType
) -> None:
    monkeypatch.setenv("AWS_STORAGE_BUCKET_NAME", "archive")
    monkeypatch.setenv("AWS_S3_REGION_NAME", "eu-central-1")
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.com")

    settings = importlib.reload(reload_settings)

    assert settings.STORAGES["default"]["BACKEND"] == "storages.backends.s3.S3Storage"
    assert settings.AWS_S3_REGION_NAME == "eu-central-1"
    assert settings.AWS_S3_ENDPOINT_URL == "https://s3.example.com"


def test_empty_s3_endpoint_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType
) -> None:
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "")

    settings = importlib.reload(reload_settings)

    assert settings.AWS_S3_ENDPOINT_URL is None


@pytest.mark.parametrize("built", [True, False])
def test_frontend_build_is_a_static_dir_only_once_built(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType, built: bool
) -> None:
    monkeypatch.setattr(Path, "is_dir", lambda self: built)

    settings = importlib.reload(reload_settings)

    expected = [settings.FRONTEND_DIST_DIR] if built else []
    assert expected == settings.STATICFILES_DIRS


def test_search_config_is_polish_unless_the_env_says_otherwise(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType
) -> None:
    monkeypatch.delenv("SEARCH_TS_CONFIG", raising=False)
    assert importlib.reload(reload_settings).SEARCH_TS_CONFIG == "polish"

    monkeypatch.setenv("SEARCH_TS_CONFIG", "simple")
    assert importlib.reload(reload_settings).SEARCH_TS_CONFIG == "simple"


PRODUCTION_ENV = {
    "DEBUG": "false",
    "SECRET_KEY": "production-secret",
    "DATABASE_URL": "postgres://db:5432/buczkovianum",
    "ALLOWED_HOSTS": "test.example.com",
    "CSRF_TRUSTED_ORIGINS": "https://test.example.com",
    "AWS_STORAGE_BUCKET_NAME": "archive",
    "AWS_S3_REGION_NAME": "eu-central-1",
    "AWS_ACCESS_KEY_ID": "AKIAEXAMPLE",
    "AWS_SECRET_ACCESS_KEY": "example-secret",
}


@pytest.fixture
def production_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in PRODUCTION_ENV.items():
        monkeypatch.setenv(name, value)


@pytest.mark.usefixtures("production_env")
@pytest.mark.parametrize("name", settings_module.PRODUCTION_REQUIRED_ENV)
@pytest.mark.parametrize("value", [None, ""])
def test_production_refuses_to_start_without_a_required_variable(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType, name: str, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(name)
    else:
        monkeypatch.setenv(name, value)

    with pytest.raises(ImproperlyConfigured, match=f"environment variable: {name}$"):
        importlib.reload(reload_settings)


@pytest.mark.parametrize("name", settings_module.REQUIRED_ENV)
def test_debug_still_needs_secret_key_and_database_url(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType, name: str
) -> None:
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.delenv(name)

    with pytest.raises(ImproperlyConfigured, match=f"environment variable: {name}$"):
        importlib.reload(reload_settings)


def test_debug_runs_without_production_variables(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType
) -> None:
    monkeypatch.setenv("DEBUG", "true")
    for name in ("ALLOWED_HOSTS", "CSRF_TRUSTED_ORIGINS", "AWS_STORAGE_BUCKET_NAME"):
        monkeypatch.delenv(name, raising=False)

    settings = importlib.reload(reload_settings)

    assert settings.STORAGES["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"


@pytest.mark.usefixtures("production_env")
def test_production_trusts_the_proxy_scheme_and_secures_cookies(
    reload_settings: ModuleType,
) -> None:
    settings = importlib.reload(reload_settings)

    assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True


@pytest.mark.usefixtures("production_env")
def test_us_ops_01_ac5_media_go_to_a_private_s3_bucket(reload_settings: ModuleType) -> None:
    settings = importlib.reload(reload_settings)

    assert settings.STORAGES["default"]["BACKEND"] == "storages.backends.s3.S3Storage"
    assert settings.AWS_DEFAULT_ACL is None
    assert settings.AWS_QUERYSTRING_AUTH is True


@pytest.mark.usefixtures("production_env")
def test_us_ops_01_ac5_media_urls_are_presigned(settings: Settings) -> None:
    settings.AWS_STORAGE_BUCKET_NAME = PRODUCTION_ENV["AWS_STORAGE_BUCKET_NAME"]
    settings.AWS_S3_REGION_NAME = PRODUCTION_ENV["AWS_S3_REGION_NAME"]
    settings.STORAGES = {
        **settings.STORAGES,
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
    }

    url = storages["default"].url("scans/czarny-potok.pdf")

    assert url.startswith("https://archive.s3.")
    assert "X-Amz-Signature=" in url
    assert "X-Amz-Expires=" in url


@pytest.mark.parametrize(("value", "expected"), [("true", True), ("TRUE", True), ("false", False)])
def test_us_ops_01_ac3_ac4_guards_come_from_env(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType, value: str, expected: bool
) -> None:
    monkeypatch.setenv("BASIC_AUTH_USER", "editor")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "s3cret")
    monkeypatch.setenv("ROBOTS_NOINDEX", value)

    settings = importlib.reload(reload_settings)

    assert (settings.BASIC_AUTH_USER, settings.BASIC_AUTH_PASSWORD) == ("editor", "s3cret")
    assert settings.ROBOTS_NOINDEX is expected
    assert settings.MIDDLEWARE[:2] == [
        "config.middleware.NoindexMiddleware",
        "config.middleware.BasicAuthMiddleware",
    ]


def test_us_ops_01_ac3_ac4_guards_are_off_without_env(
    monkeypatch: pytest.MonkeyPatch, reload_settings: ModuleType
) -> None:
    for name in ("BASIC_AUTH_USER", "BASIC_AUTH_PASSWORD", "ROBOTS_NOINDEX"):
        monkeypatch.delenv(name, raising=False)

    settings = importlib.reload(reload_settings)

    assert not settings.BASIC_AUTH_USER
    assert not settings.BASIC_AUTH_PASSWORD
    assert settings.ROBOTS_NOINDEX is False
