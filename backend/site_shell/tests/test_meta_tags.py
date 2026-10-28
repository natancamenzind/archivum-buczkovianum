"""Every public URL gets its own `<title>` and meta description (user stories §4, SEO)."""

from html.parser import HTMLParser

import pytest
from django.contrib.auth.models import User
from django.test import Client
from pytest_django import DjangoAssertNumQueries

from archive.models import Publishable, Status
from archive.tests.factories import (
    ContextualMaterialFactory,
    NoteFactory,
    SecondaryTextFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)
from site_shell.meta import DESCRIPTION, DESCRIPTION_LENGTH

pytestmark = pytest.mark.usefixtures("frontend_dist")

PUBLISHED = Status.PUBLISHED


class _Head(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.titles: list[str] = []
        self.meta: dict[str, list[str]] = {}
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "title":
            self._in_title = True
            self.titles.append("")
        elif tag == "meta" and "content" in values:
            key = values.get("name") or values.get("property") or ""
            self.meta.setdefault(key, []).append(values["content"] or "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.titles[-1] += data


def head(client: Client, url: str, status: int = 200) -> tuple[str, str]:
    """The page's one title and one meta description, after checking its status."""
    response = client.get(url)
    assert response.status_code == status
    parser = _Head()
    parser.feed(response.text)
    assert len(parser.titles) == 1
    assert parser.meta["og:title"] == parser.titles
    assert parser.meta["og:description"] == parser.meta["description"]
    [description] = parser.meta["description"]
    return parser.titles[0], description


@pytest.mark.parametrize(
    ("url", "title", "description"),
    [
        ("/", "Archivum Buczkovianum", DESCRIPTION),
        (
            "/works",
            "Utwory — Archivum Buczkovianum",
            "Wszystkie utwory Leopolda Buczkowskiego w archiwum, w kolejności wydania.",
        ),
        (
            "/typescripts/",
            "Maszynopisy — Archivum Buczkovianum",
            "Jednostki archiwalne z maszynopisami utworów, pogrupowane według utworu.",
        ),
        (
            "/tags",
            "Tagi — Archivum Buczkovianum",
            "Motywy łączące fragmenty i zapiski z różnych utworów.",
        ),
        (
            "/about",
            "O archiwum — Archivum Buczkovianum",
            "O projekcie Archivum Buczkovianum i jego zespole.",
        ),
        (
            "/About/",
            "O archiwum — Archivum Buczkovianum",
            "O projekcie Archivum Buczkovianum i jego zespole.",
        ),
        (
            "/search",
            "Wyszukiwanie — Archivum Buczkovianum",
            "Szukaj w archiwum: tytuły, opisy, transkrypcje i tagi.",
        ),
    ],
)
@pytest.mark.django_db
def test_seo_every_list_page_has_its_title_and_description(
    client: Client,
    django_assert_num_queries: DjangoAssertNumQueries,
    url: str,
    title: str,
    description: str,
) -> None:
    with django_assert_num_queries(0):
        assert head(client, url) == (title, description)


@pytest.mark.parametrize(
    ("url", "title"),
    [
        ("/search?q=dezerter", "Wyniki dla „dezerter” — Archivum Buczkovianum"),
        ("/search?q=+czarny+potok+&tab=works", "Wyniki dla „czarny potok” — Archivum Buczkovianum"),
        ("/search?tab=all", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?q=+&tab=fragments&work=3", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?work=3", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?decade=1950&decade=x", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?has_scan=1", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?has_text=1", "Wszystkie wyniki — Archivum Buczkovianum"),
        ("/search?q=", "Wyszukiwanie — Archivum Buczkovianum"),
        (
            "/search?work=abc&work=0&decade=1955&decade=1950&has_scan=true&sort=title",
            "Wyszukiwanie — Archivum Buczkovianum",
        ),
    ],
)
def test_seo_the_search_page_title_follows_its_state(client: Client, url: str, title: str) -> None:
    assert head(client, url)[0] == title


@pytest.mark.django_db
class TestEntityPages:
    def test_seo_every_entity_page_has_its_title_and_description(self, client: Client) -> None:
        published = {
            "status": PUBLISHED,
            "description": "<p>Powieść o <em>Wertepach</em>.</p><p>Drugi akapit.</p>",
        }
        entities: list[Publishable] = [
            WorkFactory.create(title="Wertepy", slug="wertepy", **published),
            TagFactory.create(title="Dezerter", slug="dezerter", **published),
            TypescriptFactory.create(title="Pierwsza wersja", **published),
            NoteFactory.create(title="Notes 18", **published),
            SecondaryTextFactory.create(title="List nr 32", **published),
            ContextualMaterialFactory.create(title="Portret", **published),
        ]

        for entity in entities:
            assert head(client, entity.get_absolute_url()) == (
                f"{entity.title} — Archivum Buczkovianum",
                "Powieść o Wertepach. Drugi akapit.",
            )

    @pytest.mark.parametrize("url", ["/works/wertepy/", "/Works/wertepy"])
    def test_seo_an_entity_url_matches_as_react_router_matches_it(
        self, client: Client, url: str
    ) -> None:
        WorkFactory.create(title="Wertepy", slug="wertepy", status=PUBLISHED)

        assert head(client, url)[0] == "Wertepy — Archivum Buczkovianum"

    def test_seo_an_entity_without_a_description_gets_the_site_description(
        self, client: Client
    ) -> None:
        work = WorkFactory.create(status=PUBLISHED, description="<p> </p>")

        assert head(client, work.get_absolute_url())[1] == DESCRIPTION

    def test_seo_a_long_description_is_shortened(self, client: Client) -> None:
        work = WorkFactory.create(status=PUBLISHED, description=f"<p>{'Słowo ' * 100}</p>")

        description = head(client, work.get_absolute_url())[1]

        assert len(description) <= DESCRIPTION_LENGTH
        assert description.startswith("Słowo Słowo")
        assert description.endswith("…")

    def test_seo_titles_and_descriptions_are_escaped(self, client: Client) -> None:
        work = WorkFactory.create(
            title='</title><script>alert("x")</script>',
            status=PUBLISHED,
            description="<p>&quot;/&gt;&lt;script&gt;</p>",
        )

        response = client.get(work.get_absolute_url())

        assert "<script>alert" not in response.text
        assert head(client, work.get_absolute_url()) == (
            '</title><script>alert("x")</script> — Archivum Buczkovianum',
            '"/><script>',
        )

    def test_r_06_a_draft_is_404_for_an_anonymous_reader(self, client: Client) -> None:
        drafts: list[Publishable] = [
            WorkFactory.create(title="Szkic utworu"),
            TagFactory.create(title="Brulion"),
            TypescriptFactory.create(),
            NoteFactory.create(),
            SecondaryTextFactory.create(),
            ContextualMaterialFactory.create(),
        ]

        for draft in drafts:
            title, _ = head(client, draft.get_absolute_url(), status=404)
            assert title == "Nie znaleziono strony — Archivum Buczkovianum"

    def test_r_06_a_draft_is_shown_to_staff(self, client: Client) -> None:
        drafts: list[Publishable] = [
            WorkFactory.create(title="Szkic utworu"),
            TagFactory.create(title="Brulion"),
            TypescriptFactory.create(title="Szkic maszynopisu"),
            NoteFactory.create(title="Szkic zapisku"),
            SecondaryTextFactory.create(title="Szkic listu"),
            ContextualMaterialFactory.create(title="Szkic materiału"),
        ]
        client.force_login(User.objects.create_user(username="editor", is_staff=True))

        for draft in drafts:
            title = head(client, draft.get_absolute_url())[0]
            assert title == f"{draft.title} — Archivum Buczkovianum"

    def test_r_06_a_draft_is_404_for_a_user_who_is_not_staff(self, client: Client) -> None:
        work = WorkFactory.create()
        client.force_login(User.objects.create_user(username="reader"))

        head(client, work.get_absolute_url(), status=404)

    @pytest.mark.parametrize(
        "url",
        [
            "/works/missing",
            "/tags/missing/",
            "/typescripts/999999",
            "/typescripts/99999999999999999999",
            "/notes/abc",
            "/notes/%EF%BC%91",  # a full-width digit one
            "/secondary-texts/-1",
            "/materials/",
            "/works/wertepy/extra",
            "/works//wertepy",
            "/works/%00",
            "/tags/zażółć",
        ],
    )
    def test_seo_an_entity_url_with_no_entity_is_404(self, client: Client, url: str) -> None:
        WorkFactory.create(slug="wertepy", status=PUBLISHED)

        title, _ = head(client, url, status=404)

        assert title == "Nie znaleziono strony — Archivum Buczkovianum"


@pytest.mark.parametrize("url", ["/unknown", "/about/team", "/search/x", "/index.html/x"])
def test_seo_an_unknown_url_is_404_with_the_frontend_not_found_page(
    client: Client, url: str
) -> None:
    title, description = head(client, url, status=404)

    assert (title, description) == ("Nie znaleziono strony — Archivum Buczkovianum", DESCRIPTION)


@pytest.mark.parametrize("url", ["/.env", "/.git/config", "/.well-known/x", "/works/.env/"])
def test_seo_a_path_with_a_dot_segment_is_404(client: Client, url: str) -> None:
    assert client.get(url).status_code == 404


def test_seo_the_404_page_keeps_the_frontend_and_its_caching(client: Client) -> None:
    response = client.get("/unknown")

    assert '<div id="root"></div>' in response.text
    assert "no-cache" in response["Cache-Control"]
