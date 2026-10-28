from pathlib import Path
from typing import Any

import pytest
from django.core.files.base import ContentFile
from django.test import Client
from django.urls import reverse
from pytest_django import DjangoAssertNumQueries
from pytest_django.fixtures import Settings

from archive.models import SiteSettings, Status
from archive.tests.factories import (
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    NoteFactory,
    SecondaryTextFactory,
    SiteSettingsFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


def home(client: Client) -> dict[str, Any]:
    response = client.get(reverse("home"))
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestHomeEndpoint:
    def test_home_is_public_and_empty_without_content(self, client: Client) -> None:
        # Act
        result = home(client)

        # Assert
        assert result == {
            "intro": "",
            "portrait": "",
            "portrait_alt": "",
            "statistics": {"works": 0, "fragments": 0, "tags": 0},
            "works": [],
            "featured": None,
            "tags": [],
        }

    def test_us_ra_01_ac2_returns_the_introduction_and_portrait(
        self, client: Client, settings: Settings, tmp_path: Path
    ) -> None:
        # Arrange
        settings.MEDIA_ROOT = tmp_path
        SiteSettingsFactory.create(
            intro_text="<p>Archiwum <em>Buczkowskiego</em>.</p>",
            portrait=ContentFile(b"img", name="portret.jpg"),
            portrait_alt="Leopold Buczkowski, portret",
        )

        # Act
        result = home(client)

        # Assert
        assert result["intro"] == "<p>Archiwum <em>Buczkowskiego</em>.</p>"
        assert result["portrait"] == "/media/site/portret.jpg"
        assert result["portrait_alt"] == "Leopold Buczkowski, portret"

    def test_us_ra_01_ac2_counts_published_works_visible_fragments_and_published_tags(
        self, client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        WorkFactory.create(status=Status.DRAFT)
        main = TypescriptFactory.create(work=work, status=PUBLISHED, is_main=True)
        other = TypescriptFactory.create(work=work, status=PUBLISHED)
        draft = TypescriptFactory.create(work=work, status=Status.DRAFT)
        FragmentFactory.create_batch(2, document=main.document)
        FragmentFactory.create(document=other.document)
        FragmentFactory.create(document=draft.document)
        FragmentFactory.create(document=SecondaryTextFactory.create(status=PUBLISHED).document)
        FragmentFactory.create(document=SecondaryTextFactory.create(status=Status.DRAFT).document)
        TagFactory.create_batch(2, status=PUBLISHED)
        TagFactory.create(status=Status.DRAFT)

        # Act
        result = home(client)

        # Assert
        assert result["statistics"] == {"works": 1, "fragments": 4, "tags": 2}

    def test_us_ra_01_ac3_lists_published_work_cards_by_first_edition(self, client: Client) -> None:
        # Arrange
        later = WorkFactory.create(status=PUBLISHED, slug="czarny-potok")
        EditionFactory.create(work=later, year=1954)
        first = WorkFactory.create(
            status=PUBLISHED, slug="wertepy", title="Wertepy", genre="powieść"
        )
        EditionFactory.create(work=first, year=1947)
        main = TypescriptFactory.create(work=first, status=PUBLISHED, is_main=True)
        FragmentFactory.create_batch(2, document=main.document)
        WorkFactory.create(status=Status.DRAFT)

        # Act
        result = home(client)

        # Assert
        assert [card["slug"] for card in result["works"]] == ["wertepy", "czarny-potok"]
        assert result["works"][0] == {
            "slug": "wertepy",
            "title": "Wertepy",
            "genre": "powieść",
            "year": 1947,
            "cover_image": "",
            "cover_image_alt": "",
            "fragment_count": 2,
        }

    def test_us_ra_01_ac4_the_cloud_has_published_tags_in_use_with_their_counts(
        self, client: Client
    ) -> None:
        # Arrange
        frequent = TagFactory.create(status=PUBLISHED, slug="wojna", title="Wojna")
        rare = TagFactory.create(status=PUBLISHED, slug="las", title="Las")
        TagFactory.create(status=PUBLISHED, title="Nieużywany")
        draft = TagFactory.create(status=Status.DRAFT, title="Szkic")
        for note in NoteFactory.create_batch(2, status=PUBLISHED):
            note.tags.add(frequent, draft)
        NoteFactory.create(status=PUBLISHED).tags.add(rare)

        # Act
        result = home(client)

        # Assert
        assert result["tags"] == [
            {"slug": "wojna", "title": "Wojna", "occurrences": 2},
            {"slug": "las", "title": "Las", "occurrences": 1},
        ]

    def test_us_ra_01_ac5_an_edited_introduction_and_portrait_show_at_once(
        self, client: Client, settings: Settings, tmp_path: Path
    ) -> None:
        # Arrange
        settings.MEDIA_ROOT = tmp_path
        site = SiteSettings.load()
        site.portrait = ContentFile(b"img", name="stary.jpg")
        site.save()
        home(client)
        site.intro_text = "<p>Nowy wstęp.</p>"
        site.portrait = ContentFile(b"img", name="nowy.jpg")
        site.portrait_alt = "Nowy portret"
        site.save()

        # Act
        result = home(client)

        # Assert
        assert result["intro"] == "<p>Nowy wstęp.</p>"
        assert result["portrait"] == "/media/site/nowy.jpg"
        assert result["portrait_alt"] == "Nowy portret"

    def test_us_ra_02_ac1_features_a_visible_featured_fragment_as_a_card(
        self, client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED, title="Wertepy")
        main = TypescriptFactory.create(work=work, status=PUBLISHED, is_main=True)
        draft = TypescriptFactory.create(work=work, status=Status.DRAFT)
        FragmentFactory.create(document=main.document, start=0, end=5)
        featured = FragmentFactory.create(
            document=main.document, start=6, end=12, is_featured=True, location="rozdział I"
        )
        FragmentFactory.create(document=draft.document, is_featured=True)

        # Act
        result = home(client)

        # Assert
        card = result["featured"]["fragment"]
        assert card["id"] == featured.pk
        assert card["url"] == f"/typescripts/{main.pk}?fragment={featured.pk}"
        assert card["work"] == "Wertepy"
        assert card["number"] == 2
        assert card["location"] == "rozdział I"

    def test_us_ra_02_ac1_picks_at_random_among_the_featured_fragments(
        self, client: Client
    ) -> None:
        # Arrange
        main = TypescriptFactory.create(status=PUBLISHED, is_main=True)
        featured = {
            FragmentFactory.create(document=main.document, start=start, is_featured=True).pk
            for start in range(3)
        }

        # Act
        picked = {home(client)["featured"]["fragment"]["id"] for _ in range(30)}

        # Assert
        assert len(picked) > 1
        assert picked <= featured

    def test_us_ra_02_ac1_features_nothing_without_a_visible_featured_fragment(
        self, client: Client
    ) -> None:
        # Arrange
        main = TypescriptFactory.create(status=PUBLISHED, is_main=True)
        FragmentFactory.create(document=main.document)
        draft = TypescriptFactory.create(status=Status.DRAFT)
        FragmentFactory.create(document=draft.document, is_featured=True)

        # Act
        result = home(client)

        # Assert
        assert result["featured"] is None

    def test_us_ra_02_ac2_names_the_work_with_the_fragments_search_finds_in_it(
        self, client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED, title="Wertepy")
        EditionFactory.create(work=work, year=1947)
        main = TypescriptFactory.create(work=work, status=PUBLISHED, is_main=True)
        FragmentFactory.create(document=main.document, start=0, is_featured=True)
        FragmentFactory.create(document=main.document, start=1)
        note = NoteFactory.create(status=PUBLISHED, document=DocumentFactory.create())
        note.works.add(work)
        note.save()
        FragmentFactory.create(document=note.document)
        FragmentFactory.create(document=TypescriptFactory.create(status=PUBLISHED).document)

        # Act
        result = home(client)

        # Assert
        found = client.get(reverse("search"), {"tab": "fragments", "work": str(work.pk)}).json()
        assert found["total"] == 3
        assert result["featured"]["work"] == {"id": work.pk, "title": "Wertepy", "count": 3}

    def test_us_ra_02_ac2_names_the_first_published_work_of_the_source(
        self, client: Client
    ) -> None:
        # Arrange
        later = WorkFactory.create(status=PUBLISHED, title="Czarny potok")
        EditionFactory.create(work=later, year=1954)
        earlier = WorkFactory.create(status=PUBLISHED, title="Wertepy")
        EditionFactory.create(work=earlier, year=1947)
        note = NoteFactory.create(status=PUBLISHED, document=DocumentFactory.create())
        note.works.add(later, earlier, WorkFactory.create(status=Status.DRAFT))
        note.save()
        FragmentFactory.create(document=note.document, is_featured=True)

        # Act
        result = home(client)

        # Assert
        assert result["featured"]["fragment"]["work"] == "Wertepy, Czarny potok"
        assert result["featured"]["work"] == {"id": earlier.pk, "title": "Wertepy", "count": 1}

    def test_us_ra_02_ac2_names_no_work_when_the_source_has_none(self, client: Client) -> None:
        # Arrange
        note = NoteFactory.create(status=PUBLISHED, document=DocumentFactory.create())
        note.works.add(WorkFactory.create(status=Status.DRAFT))
        FragmentFactory.create(document=note.document, is_featured=True)

        # Act
        result = home(client)

        # Assert
        assert result["featured"]["work"] is None

    @pytest.mark.parametrize("method", ("post", "put", "patch", "delete"))
    def test_home_rejects_writes(self, client: Client, method: str) -> None:
        # Arrange
        url = reverse("home")

        # Act
        response = getattr(client, method)(url)

        # Assert
        assert response.status_code == 405

    def test_performance_home_query_count_does_not_grow_with_content(
        self, client: Client, django_assert_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        def add_work() -> None:
            work = WorkFactory.create(status=PUBLISHED)
            EditionFactory.create(work=work)
            main = TypescriptFactory.create(work=work, status=PUBLISHED, is_main=True)
            tag = TagFactory.create(status=PUBLISHED)
            FragmentFactory.create(document=main.document, is_featured=True).tags.add(tag)

        add_work()
        home(client)
        with django_assert_num_queries(9):
            home(client)
        for _ in range(5):
            add_work()

        # Act & Assert
        with django_assert_num_queries(9):
            result = home(client)

        assert len(result["works"]) == 6


class TestHomeSchema:
    def test_schema_marks_every_home_field_as_present(self, client: Client) -> None:
        # Arrange
        url = reverse("schema")

        # Act
        schemas = client.get(url, {"format": "json"}).json()["components"]["schemas"]

        # Assert
        assert sorted(schemas["HomePage"]["required"]) == [
            "featured",
            "intro",
            "portrait",
            "portrait_alt",
            "statistics",
            "tags",
            "works",
        ]
        assert sorted(schemas["HomeStatistics"]["required"]) == ["fragments", "tags", "works"]
