import base64

import pytest
from django.test import Client
from pytest_django.fixtures import Settings

# Any URL behind basic auth that answers 200 without data.
PAGE = "/api/schema/"


def basic(user: str, password: str) -> str:
    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()


@pytest.fixture
def basic_auth(settings: Settings) -> None:
    settings.BASIC_AUTH_USER = "editor"
    settings.BASIC_AUTH_PASSWORD = "s3cret"


@pytest.mark.usefixtures("basic_auth")
@pytest.mark.parametrize("url", [PAGE, "/admin/", "/", "/works"])
def test_us_ops_01_ac3_no_credentials_is_401(client: Client, url: str) -> None:
    response = client.get(url)

    assert response.status_code == 401
    assert response["WWW-Authenticate"].startswith('Basic realm="Archivum Buczkovianum"')


@pytest.mark.usefixtures("basic_auth")
@pytest.mark.parametrize(
    "authorization",
    [
        basic("editor", "wrong"),
        basic("someone", "s3cret"),
        basic("editor", "s3cret-and-more"),
        "Basic not-base64!",
        "Bearer s3cret",
    ],
)
def test_us_ops_01_ac3_wrong_credentials_are_401(client: Client, authorization: str) -> None:
    response = client.get(PAGE, HTTP_AUTHORIZATION=authorization)

    assert response.status_code == 401
    assert "WWW-Authenticate" in response


@pytest.mark.usefixtures("basic_auth")
def test_us_ops_01_ac3_right_credentials_are_200(client: Client) -> None:
    response = client.get(PAGE, HTTP_AUTHORIZATION=basic("editor", "s3cret"))

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("basic_auth")
def test_us_ops_01_ac3_healthz_is_exempt(client: Client) -> None:
    response = client.get("/healthz")

    assert response.status_code == 200


@pytest.mark.parametrize(("user", "password"), [("", ""), ("editor", ""), ("", "s3cret")])
def test_us_ops_01_ac3_basic_auth_is_off_unless_both_are_set(
    client: Client, settings: Settings, user: str, password: str
) -> None:
    settings.BASIC_AUTH_USER = user
    settings.BASIC_AUTH_PASSWORD = password

    response = client.get(PAGE)

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.usefixtures("basic_auth")
@pytest.mark.parametrize(("url", "status"), [("/healthz", 200), (PAGE, 401)])
def test_us_ops_01_ac4_noindex_header_is_on_every_response(
    client: Client, settings: Settings, url: str, status: int
) -> None:
    settings.ROBOTS_NOINDEX = True

    response = client.get(url)

    assert response.status_code == status
    assert response["X-Robots-Tag"] == "noindex, nofollow"


@pytest.mark.django_db
def test_us_ops_01_ac4_no_noindex_header_when_off(client: Client, settings: Settings) -> None:
    settings.ROBOTS_NOINDEX = False

    response = client.get("/healthz")

    assert "X-Robots-Tag" not in response
