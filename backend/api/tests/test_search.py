from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from archive.models import ContentKind, Status, Work
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED
GROUPS = ("works", "tags", "fragments", "notes", "typescripts", "secondary_texts", "materials")


def results(client: Client, q: str, **params: str) -> dict[str, Any]:
    response = client.get(reverse("search"), {"q": q, **params})
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


def titles(page: dict[str, Any], group: str) -> list[str]:
    return [result["title"] for result in page[group]]


def published_work(title: str, year: int, **kwargs: Any) -> Work:
    work = WorkFactory.create(status=PUBLISHED, title=title, **kwargs)
    EditionFactory.create(work=work, year=year)
    return work


@pytest.fixture
def archive() -> Work:
    """ "Dezerter" in every kind of entity; the work "Wertepy" has two matching fragments."""
    wertepy = published_work("Wertepy", 1947, slug="wertepy", description="Dezerter w lesie.")
    TagFactory.create(status=PUBLISHED, title="Dezerter", slug="dezerter")
    typescript = TypescriptFactory.create(
        status=PUBLISHED,
        work=wertepy,
        title="Maszynopis Wertepów",
        shelfmark="1618",
        institution=InstitutionFactory.create(),
        document__text="Szedł dezerter przez las. Dezerter wrócił.",
    )
    FragmentFactory.create(document=typescript.document, start=6, end=14)
    FragmentFactory.create(document=typescript.document, start=26, end=34)
    FragmentFactory.create(document=typescript.document, start=21, end=24)
    note = NoteFactory.create(
        status=PUBLISHED,
        title="Notes 18",
        content_kind=ContentKind.PLAIN_TEXT,
        external_url="",
        document=DocumentFactory.create(text="Notatka o dezerterze: dezerter."),
    )
    note.works.add(wertepy)
    SecondaryTextFactory.create(
        status=PUBLISHED, title="Recenzja", description="Dezerter w recenzji."
    )
    ContextualMaterialFactory.create(status=PUBLISHED, title="Dezerter na zdjęciu")
    return wertepy


@pytest.mark.django_db
class TestSearchEndpoint:
    def test_us_ra_15_ac2_returns_the_total_of_all_groups(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        assert page["total"] == 8
        assert page["total"] == sum(len(page[group]) for group in GROUPS)

    def test_us_ra_15_ac3_results_come_grouped_by_type(self, client: Client, archive: Work) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        assert {group: len(page[group]) for group in GROUPS} == {
            "works": 1,
            "tags": 1,
            "fragments": 2,
            "notes": 1,
            "typescripts": 1,
            "secondary_texts": 1,
            "materials": 1,
        }

    def test_us_ra_15_ac4_sorted_by_relevance_or_by_title(self, client: Client) -> None:
        # Arrange
        published_work("Wertepy", 1947, description="Las, las i las.")
        published_work("Zielony las", 1950)

        # Act
        by_relevance = results(client, "las")
        by_title = results(client, "las", sort="title")

        # Assert
        assert titles(by_relevance, "works") == ["Zielony las", "Wertepy"]
        assert titles(by_title, "works") == ["Wertepy", "Zielony las"]

    def test_us_ra_15_ac5_a_work_shows_genre_year_and_its_matching_fragments(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        assert page["works"] == [
            {
                "url": "/works/wertepy",
                "title": "Wertepy",
                "genre": "powieść",
                "year": 1947,
                "fragments": 2,
            }
        ]

    def test_us_ra_15_ac5_a_fragment_result_is_a_fragment_card(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        card = next(card for card in page["fragments"] if card["quote"] == "dezerter")
        assert card["number"] == 1
        assert card["source_type"] == "typescript"
        assert card["work"] == "Wertepy"
        assert card["url"].startswith("/typescripts/")
        assert "?fragment=" in card["url"]

    def test_us_ra_15_ac5_each_result_says_its_type_and_links_to_its_page(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        typescript = page["typescripts"][0]
        assert typescript["title"] == "Maszynopis Wertepów"
        assert typescript["shelfmark"] == "ML, sygn. 1618"
        assert typescript["url"].startswith("/typescripts/")
        assert page["notes"][0]["url"].startswith("/notes/")
        assert page["secondary_texts"][0]["url"].startswith("/secondary-texts/")
        assert page["materials"][0]["url"].startswith("/materials/")
        assert page["tags"][0]["url"] == "/tags/dezerter"
        assert page["tags"][0]["occurrences"] == 0

    def test_us_ra_15_ac6_a_text_match_has_a_snippet_and_opens_at_the_match(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "dezerter")

        # Assert
        typescript = page["typescripts"][0]
        assert "<mark>dezerter</mark>" in typescript["snippet"]
        assert typescript["url"].endswith("?q=dezerter")
        assert "snippet" not in page["works"][0]

    def test_us_ra_15_ac6_found_by_a_tag_name_only_the_snippet_is_unmarked(
        self, client: Client
    ) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED, title="Dezerter")
        note = NoteFactory.create(status=PUBLISHED, title="Notes 18", description="Opis zapisku.")
        note.tags.add(tag)
        note.save()

        # Act
        page = results(client, "dezerter")

        # Assert
        assert page["notes"] == [
            {
                "url": note.get_absolute_url(),
                "title": "Notes 18",
                "shelfmark": "",
                "snippet": "Opis zapisku.",
            }
        ]

    def test_d27_relation_tags_are_not_searched(self, client: Client) -> None:
        # Arrange
        tag = TagFactory.create(status=PUBLISHED, title="Dezerter")
        link = SecondaryTextWorkLinkFactory.create(
            secondary_text__status=PUBLISHED, work__status=PUBLISHED
        )
        link.tags.add(tag)
        link.secondary_text.save()

        # Act
        page = results(client, "dezerter")

        # Assert
        assert page["secondary_texts"] == []

    def test_us_ra_15_ac8_no_results_suggest_the_three_most_frequent_tags(
        self, client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        typescript = TypescriptFactory.create(status=PUBLISHED, work=work)
        tags = [TagFactory.create(status=PUBLISHED, title=f"Tag {n}") for n in range(4)]
        for count, tag in zip((1, 2, 0, 2), tags, strict=True):
            for carrier in (work, typescript)[:count]:
                carrier.tags.add(tag)

        # Act
        page = results(client, "nieistniejące")

        # Assert
        assert page["total"] == 0
        assert [(tag["title"], tag["occurrences"]) for tag in page["suggested_tags"]] == [
            ("Tag 1", 2),
            ("Tag 3", 2),
            ("Tag 0", 1),
        ]

    def test_us_ra_15_a_query_of_only_stopwords_returns_everything(
        self, client: Client, archive: Work
    ) -> None:
        # Act
        page = results(client, "-")

        # Assert
        assert page["total"] > 8
        assert page["suggested_tags"] == []
