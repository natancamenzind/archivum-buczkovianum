import importlib
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest

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
