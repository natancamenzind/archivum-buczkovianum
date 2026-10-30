from types import SimpleNamespace
from typing import NoReturn

import pytest
from django.db import OperationalError
from django.test import Client
from pytest_django.fixtures import Settings

from config import healthz as healthz_module


@pytest.mark.django_db
def test_us_ops_01_ac6_healthz_is_200_when_the_database_answers(client: Client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert response["Content-Type"].startswith("text/plain")


def test_us_ops_01_ac6_healthz_is_503_when_the_database_is_down(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreachable() -> NoReturn:
        raise OperationalError("could not connect to server")

    monkeypatch.setattr(healthz_module, "connection", SimpleNamespace(cursor=unreachable))

    response = client.get("/healthz")

    assert response.status_code == 503


@pytest.mark.django_db
def test_us_ops_01_ac6_healthz_answers_a_host_that_is_not_allowed(
    client: Client, settings: Settings
) -> None:
    settings.ALLOWED_HOSTS = ["test.example.com"]

    health = client.get("/healthz", HTTP_HOST="10.0.0.5:10000")
    page = client.get("/api/schema/", HTTP_HOST="10.0.0.5:10000")

    assert health.status_code == 200
    assert page.status_code == 400


def test_us_ops_01_ac6_healthz_is_503_for_a_host_that_is_not_allowed(
    client: Client, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unreachable() -> NoReturn:
        raise OperationalError("could not connect to server")

    settings.ALLOWED_HOSTS = ["test.example.com"]
    monkeypatch.setattr(healthz_module, "connection", SimpleNamespace(cursor=unreachable))

    response = client.get("/healthz", HTTP_HOST="10.0.0.5:10000")

    assert response.status_code == 503


@pytest.mark.django_db
def test_us_ops_01_ac6_healthz_needs_no_basic_auth(client: Client, settings: Settings) -> None:
    settings.BASIC_AUTH_USER = "editor"
    settings.BASIC_AUTH_PASSWORD = "s3cret"

    health = client.get("/healthz")
    page = client.get("/api/schema/")

    assert health.status_code == 200
    assert page.status_code == 401


def test_us_ops_01_ac6_healthz_accepts_only_get_and_head(client: Client) -> None:
    response = client.post("/healthz")

    assert response.status_code == 405
