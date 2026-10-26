from pathlib import Path

import pytest
from pytest_django.fixtures import Settings


@pytest.fixture(autouse=True)
def _media_in_tmp(settings: Settings, tmp_path: Path) -> None:
    """Uploaded test files go to a temporary directory, not the project's media folder."""
    settings.MEDIA_ROOT = tmp_path
