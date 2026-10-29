from types import TracebackType

import pytest
from django.db import OperationalError
from django.test import Client

from config import healthz as healthz_module


class _UnreachableDatabase:
    """Stands in for `django.db.connection` when the database server is down."""

    def cursor(self) -> "_UnreachableDatabase":
        return self

    def __enter__(self) -> "_UnreachableDatabase":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def execute(self, sql: str) -> None:
        raise OperationalError("could not connect to server")


@pytest.mark.django_db
def test_us_ops_01_ac6_healthz_is_200_when_the_database_answers(client: Client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.content == b"ok"
    assert response["Content-Type"].startswith("text/plain")


def test_us_ops_01_ac6_healthz_is_503_when_the_database_is_down(
    client: Client, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(healthz_module, "connection", _UnreachableDatabase())

    response = client.get("/healthz")

    assert response.status_code == 503


def test_us_ops_01_ac6_healthz_is_not_in_the_api_schema(client: Client) -> None:
    response = client.get("/api/schema/")

    assert b"healthz" not in response.content
