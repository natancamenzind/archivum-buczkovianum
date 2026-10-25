import pytest
from pytest_django.fixtures import Settings


@pytest.fixture(autouse=True)
def _plain_static_storage(settings: Settings) -> None:
    """Tests run without collectstatic, so the manifest storage has nothing to read."""
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
