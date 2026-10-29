import base64

import pytest
from django.conf import settings
from django.test import Client


def test_api_authenticates_only_with_the_session() -> None:
    assert settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] == [
        "rest_framework.authentication.SessionAuthentication"
    ]


@pytest.mark.django_db
def test_api_ignores_the_proxy_basic_auth_credentials(client: Client) -> None:
    credentials = base64.b64encode(b"tester:proxy-password").decode()

    response = client.get("/api/works/", HTTP_AUTHORIZATION=f"Basic {credentials}")

    assert response.status_code == 200
