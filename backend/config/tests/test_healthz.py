from types import SimpleNamespace
from typing import NoReturn

import pytest
from django.db import OperationalError
from django.test import Client

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
