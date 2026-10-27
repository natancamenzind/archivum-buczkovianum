"""Repo-root `.env` fills os.environ for bare `uv run manage.py` (Make already exports it)."""

import os
from pathlib import Path

import pytest

from config.dotenv import load_dotenv


def test_load_dotenv_sets_unset_keys(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=from-file\n# comment\nDEBUG=true\n", encoding="utf-8")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    load_dotenv(env_file)

    assert os.environ["SECRET_KEY"] == "from-file"
    assert os.environ["DEBUG"] == "true"


def test_load_dotenv_does_not_override_existing_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET_KEY=from-file\n", encoding="utf-8")
    monkeypatch.setenv("SECRET_KEY", "already-set")

    load_dotenv(env_file)

    assert os.environ["SECRET_KEY"] == "already-set"


def test_load_dotenv_missing_file_is_a_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)

    load_dotenv(tmp_path / "missing.env")

    assert "SECRET_KEY" not in os.environ
