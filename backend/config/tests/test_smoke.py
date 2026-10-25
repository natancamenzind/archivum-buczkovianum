import pytest
from django.test import Client


@pytest.mark.django_db
def test_admin_login_page_responds(client: Client) -> None:
    response = client.get("/admin/login/")

    assert response.status_code == 200


def test_openapi_schema_responds(client: Client) -> None:
    response = client.get("/api/schema/")

    assert response.status_code == 200
    assert b"Archivum Buczkovianum API" in response.content
