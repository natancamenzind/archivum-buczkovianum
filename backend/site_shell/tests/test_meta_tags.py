"""Every public URL gets its own `<title>` and meta description (user stories §5, SEO)."""

from html.parser import HTMLParser

import pytest
from django.contrib.auth.models import User
from django.test import Client
from factory.django import DjangoModelFactory
from pytest_django import DjangoAssertNumQueries

from archive.models import Publishable, Status
from archive.tests.factories import (
    BibliographyEntryFactory,
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
ENTITY_FACTORIES = [
    WorkFactory,
    TagFactory,
    TypescriptFactory,
    NoteFactory,
    SecondaryTextFactory,
    ContextualMaterialFactory,
]


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
            "/utwory",
            "Utwory — Archivum Buczkovianum",
            "Wszystkie utwory Leopolda Buczkowskiego w archiwum, w kolejności wydania.",
        ),
        (
            "/maszynopisy/",
            "Maszynopisy — Archivum Buczkovianum",
            "Jednostki archiwalne z maszynopisami utworów, pogrupowane według utworu.",
        ),
        (
            "/tagi",
            "Tagi — Archivum Buczkovianum",
            "Motywy łączące fragmenty i zapiski z różnych utworów.",
        ),
        (
            "/o-archiwum",
            "O archiwum — Archivum Buczkovianum",
            "O projekcie Archivum Buczkovianum i jego zespole.",
        ),
        (
            "/O-Archiwum/",
            "O archiwum — Archivum Buczkovianum",
            "O projekcie Archivum Buczkovianum i jego zespole.",
        ),
        (
            "/szukaj",
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
    ("url", "name"),
    [
        ("/szukaj?q=dezerter", "Wyniki dla „dezerter”"),
        ("/szukaj?q=+czarny+potok+&tab=works", "Wyniki dla „czarny potok”"),
        ("/szukaj?tab=all", "Wszystkie wyniki"),
        ("/szukaj?q=+&tab=fragments&work=3", "Wszystkie wyniki"),
        ("/szukaj?work=3", "Wszystkie wyniki"),
        ("/szukaj?decade=1950&decade=x", "Wszystkie wyniki"),
        ("/szukaj?has_scan=1", "Wszystkie wyniki"),
        ("/szukaj?has_text=1", "Wszystkie wyniki"),
        ("/szukaj?q=", "Wyszukiwanie"),
        ("/szukaj?q=abc&q=", "Wyniki dla „abc”"),
        ("/szukaj?q=&q=abc", "Wyszukiwanie"),
        ("/szukaj?has_scan=1&has_scan=0", "Wszystkie wyniki"),
        ("/szukaj?has_text=0&has_text=1", "Wyszukiwanie"),
        ("/szukaj?work=2147483648&decade=32770", "Wyszukiwanie"),
        (f"/szukaj?work={'1' * 5000}&decade={'1' * 5000}", "Wyszukiwanie"),
        (
            "/szukaj?work=abc&work=0&decade=1955&decade=1950&has_scan=true&sort=title",
            "Wyszukiwanie",
        ),
    ],
)
def test_seo_the_search_page_title_follows_its_state(client: Client, url: str, name: str) -> None:
    assert head(client, url)[0] == f"{name} — Archivum Buczkovianum"


@pytest.mark.django_db
class TestEntityPages:
    @pytest.mark.parametrize("factory", [f for f in ENTITY_FACTORIES if f is not NoteFactory])
    def test_seo_every_entity_page_has_its_title_and_description(
        self, client: Client, factory: type[DjangoModelFactory[Publishable]]
    ) -> None:
        entity = factory.create(
            title="Wertepy",
            status=PUBLISHED,
            description="<p>Powieść o <em>Wertepach</em>.</p><p>Drugi akapit.</p>",
        )

        assert head(client, entity.get_absolute_url()) == (
            "Wertepy — Archivum Buczkovianum",
            "Powieść o Wertepach. Drugi akapit.",
        )

    def test_arc_35_a_note_page_gets_the_site_description(self, client: Client) -> None:
        note = NoteFactory.create(title="Notes 18", status=PUBLISHED)

        assert head(client, note.get_absolute_url()) == (
            "Notes 18 — Archivum Buczkovianum",
            DESCRIPTION,
        )

    @pytest.mark.parametrize("url", ["/utwory/wertepy/", "/utwory/wertepy//", "/Utwory/wertepy"])
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

    @pytest.mark.parametrize("factory", ENTITY_FACTORIES)
    def test_r_06_a_draft_is_404_for_an_anonymous_reader(
        self, client: Client, factory: type[DjangoModelFactory[Publishable]]
    ) -> None:
        draft = factory.create()

        title, _ = head(client, draft.get_absolute_url(), status=404)

        assert title == "Nie znaleziono strony — Archivum Buczkovianum"

    @pytest.mark.parametrize("factory", ENTITY_FACTORIES)
    def test_r_06_a_draft_is_shown_to_staff(
        self, client: Client, factory: type[DjangoModelFactory[Publishable]]
    ) -> None:
        draft = factory.create(title="Szkic")
        client.force_login(User.objects.create_user(username="editor", is_staff=True))

        assert head(client, draft.get_absolute_url())[0] == "Szkic — Archivum Buczkovianum"

    def test_r_06_a_draft_is_404_for_a_user_who_is_not_staff(self, client: Client) -> None:
        work = WorkFactory.create()
        client.force_login(User.objects.create_user(username="reader"))

        head(client, work.get_absolute_url(), status=404)

    @pytest.mark.parametrize(
        "url",
        [
            "/utwory/missing",
            "/tagi/missing/",
            "/maszynopisy/999999",
            "/maszynopisy/2147483648",
            "/maszynopisy/99999999999999999999",
            f"/maszynopisy/{'1' * 5000}",
            "/zapiski/abc",
            "/zapiski/%EF%BC%91",  # a full-width digit one
            "/teksty-sekundarne/-1",
            "/materialy/",
            "/utwory/wertepy/extra",
            "/utwory//wertepy",
            "/utwory/%00",
            "/tagi/zażółć",
        ],
    )
    def test_seo_an_entity_url_with_no_entity_is_404(self, client: Client, url: str) -> None:
        WorkFactory.create(slug="wertepy", status=PUBLISHED)

        title, _ = head(client, url, status=404)

        assert title == "Nie znaleziono strony — Archivum Buczkovianum"


@pytest.mark.django_db
class TestBibliographyPage:
    @pytest.mark.parametrize(
        "url",
        [
            "/utwory/wertepy/bibliografia",
            "/utwory/wertepy/bibliografia/",
            "/Utwory/wertepy/Bibliografia",
        ],
    )
    def test_us_ra_21_ac2_the_bibliography_page_has_its_title_and_description(
        self, client: Client, url: str
    ) -> None:
        work = WorkFactory.create(title="Wertepy", slug="wertepy", status=PUBLISHED)
        BibliographyEntryFactory.create(work=work)

        assert head(client, url) == (
            "Bibliografia utworu „Wertepy” — Archivum Buczkovianum",
            "Bibliografia utworu „Wertepy” Leopolda Buczkowskiego.",
        )

    def test_us_ra_21_ac5_a_work_without_entries_has_no_bibliography_page(
        self, client: Client
    ) -> None:
        work = WorkFactory.create(status=PUBLISHED)

        head(client, f"{work.get_absolute_url()}/bibliografia", status=404)

    def test_us_ra_21_ac5_a_draft_works_bibliography_is_404_for_a_reader(
        self, client: Client
    ) -> None:
        entry = BibliographyEntryFactory.create()

        head(client, f"{entry.work.get_absolute_url()}/bibliografia", status=404)

    def test_us_ra_21_ac5_a_draft_works_bibliography_is_shown_to_staff(
        self, client: Client
    ) -> None:
        entry = BibliographyEntryFactory.create(work__title="Szkic")
        client.force_login(User.objects.create_user(username="editor", is_staff=True))

        title, _ = head(client, f"{entry.work.get_absolute_url()}/bibliografia")

        assert title == "Bibliografia utworu „Szkic” — Archivum Buczkovianum"

    @pytest.mark.parametrize(
        "url", ["/utwory/missing/bibliografia", "/utwory/wertepy/bibliografia/x"]
    )
    def test_seo_a_bibliography_url_with_no_page_is_404(self, client: Client, url: str) -> None:
        BibliographyEntryFactory.create(work__slug="wertepy", work__status=PUBLISHED)

        head(client, url, status=404)


@pytest.mark.parametrize("url", ["/unknown", "/o-archiwum/team", "/szukaj/x", "/index.html/x"])
def test_seo_an_unknown_url_is_404_with_the_frontend_not_found_page(
    client: Client, url: str
) -> None:
    title, description = head(client, url, status=404)

    assert (title, description) == ("Nie znaleziono strony — Archivum Buczkovianum", DESCRIPTION)


@pytest.mark.parametrize("url", ["/.env", "/.git/config", "/.well-known/x", "/utwory/.env/"])
def test_seo_a_path_with_a_dot_segment_is_404(client: Client, url: str) -> None:
    assert client.get(url).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path",
    [
        "/works",
        "/works/wertepy",
        "/works/wertepy/bibliography",
        "/utwory/wertepy/bibliography",
        "/typescripts",
        "/tags",
        "/tags/dezerter",
        "/about",
        "/search?q=dezerter",
    ],
)
def test_arc_14_english_page_urls_are_404(client: Client, path: str) -> None:
    work = WorkFactory.create(slug="wertepy", status=PUBLISHED)
    BibliographyEntryFactory.create(work=work)
    TagFactory.create(slug="dezerter", status=PUBLISHED)

    title, _ = head(client, path, status=404)

    assert title == "Nie znaleziono strony — Archivum Buczkovianum"
