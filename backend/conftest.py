from pathlib import Path

import pytest
from pytest_django.fixtures import Settings


@pytest.fixture(autouse=True)
def _plain_static_storage(settings: Settings) -> None:
    """Tests run without collectstatic, so the manifest storage has nothing to read."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture(autouse=True)
def _static_root(settings: Settings, tmp_path: Path) -> None:
    """WhiteNoise warns when STATIC_ROOT is missing, and tests run without collectstatic."""
    settings.STATIC_ROOT = tmp_path / "staticfiles"
    settings.STATIC_ROOT.mkdir()
