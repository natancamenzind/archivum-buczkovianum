"""`manage.py load_demo_data`: the sample archive of design/rules.md (docs/plan.md, step 5)."""

import re
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from archive.management.commands import load_demo_data
from archive.management.commands.load_demo_data import spread_sentences
from archive.models import Document, Fragment, Status, Tag, Typescript, Work
from archive.tests.factories import (
    InstitutionFactory,
    SiteSettingsFactory,
    TagFactory,
    TeamMemberFactory,
    WorkFactory,
)
from search.models import SearchEntry


def index() -> set[tuple[object, ...]]:
    """Every entry with what the filters and snippets use."""
    fields = ("entity_type", "entity_id", "url", "body", "work_ids", "decades", "has_scan")
    rows = SearchEntry.objects.values_list(*fields)
    return {tuple(tuple(v) if isinstance(v, list) else v for v in row) for row in rows}


@pytest.fixture
def demo() -> str:
    output = StringIO()
    call_command("load_demo_data", stdout=output)
    return output.getvalue()


@pytest.mark.django_db
class TestDemoData:
    def test_loads_the_numbers_of_the_design(self, demo: str) -> None:
        # Arrange
        works = Work.objects.published().with_year()

        # Act
        summary = [(work.title, work.year) for work in works]

        # Assert
        assert demo == "Loaded 4 works, 62 fragments and 12 tags.\n"
        assert summary == [
            ("Wertepy", 1947),
            ("Czarny potok", 1954),
            ("Dorycki krużganek", 1957),
            ("Pierwsza świetność", 1966),
        ]
        assert Typescript.objects.published().count() == 5

    def test_tags_have_the_occurrences_of_the_design(self, demo: str) -> None:
        # Arrange
        tags = Tag.objects.published().with_occurrences()

        # Act
        occurrences = {tag.title: tag.occurrences for tag in tags}
        dezerter = Work.objects.published().referred_to_by(Tag.objects.get(title="Dezerter"))

        # Assert
        assert occurrences == {
            "Dezerter": 4,
            "Epidemia": 7,
            "Las": 6,
            "Pamięć": 18,
            "Pisanie": 3,
            "Podole": 15,
            "Stodoła": 2,
            "Szkoła": 3,
            "Ucieczka": 11,
            "Wieś": 24,
            "Wojna": 31,
            "Zima": 2,
        }
        assert {work.title for work in dezerter} == {"Wertepy", "Czarny potok"}
        assert Tag.objects.get(title="Brulion").status == Status.DRAFT

    def test_the_featured_fragment_is_the_one_on_the_home_page(self, demo: str) -> None:
        # Arrange
        main = Typescript.objects.get(work__slug="wertepy", is_main=True)

        # Act
        result = Fragment.objects.filter(document=main.document).preview()
        tags = {f.shelfmark: {tag.title for tag in f.tags.all()} for f in result.items}

        # Assert
        assert result.total == 24
        assert [f.shelfmark_display for f in result.items] == [
            "ML, sygn. 1618.0009",
            "ML, sygn. 1618.0019",
        ]
        assert result.items[0].location == "rozdział I"
        assert tags == {"1618.0009": {"Dezerter", "Epidemia"}, "1618.0019": {"Dezerter"}}

    def test_every_scan_has_as_many_pages_as_its_ocr_text(self, demo: str) -> None:
        # Arrange
        documents = Document.objects.filter(kind=Document.Kind.OCR)

        # Act
        pages = {}
        for document in documents:
            with document.scan.open("rb") as scan:
                pages[document.scan.name] = (
                    len(re.findall(rb"/Type /Page\b", scan.read())),
                    document.page_count,
                )

        # Assert
        assert len(pages) == 6
        assert all(scan == text and scan > 1 for scan, text in pages.values())

    def test_the_search_index_is_filled_as_by_saving(self, demo: str) -> None:
        # Arrange
        loaded = index()

        # Act
        call_command("rebuild_search_index", stdout=StringIO())

        # Assert
        assert index() == loaded
        assert len(loaded) == 4 + 12 + 62 + 5 + 1 + 2 + 1

    @pytest.mark.parametrize(
        "factory",
        [WorkFactory, TagFactory, InstitutionFactory, TeamMemberFactory, SiteSettingsFactory],
    )
    def test_refuses_an_archive_that_is_not_empty(self, factory: type[WorkFactory]) -> None:
        # Arrange
        factory.create()

        # Act
        with pytest.raises(CommandError, match="not empty"):
            call_command("load_demo_data", stdout=StringIO())

        # Assert
        assert not Typescript.objects.exists()

    def test_needs_the_design_images(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Arrange
        monkeypatch.setattr(load_demo_data, "IMAGES_DIR", tmp_path / "missing")

        # Act
        with pytest.raises(CommandError, match="design export"):
            call_command("load_demo_data", stdout=StringIO())

        # Assert
        assert not Work.objects.exists()


class TestSpreadSentences:
    def test_fragments_spread_over_whole_sentences(self) -> None:
        # Arrange
        text = "cięte zdanie. Pierwsze. - Pytanie? - spytał. Drugie. Trzecie. Czwarte."

        # Act
        sentences = [match.group() for match in spread_sentences(text, 2)]

        # Assert
        assert sentences == ["Pierwsze.", "Drugie."]

    def test_a_text_too_short_for_its_fragments_is_an_error(self) -> None:
        # Arrange
        text = "Jedno. Drugie."

        # Act
        with pytest.raises(CommandError, match="2 sentences, not 3"):
            spread_sentences(text, 3)

        # Assert
        assert len(spread_sentences(text, 2)) == 2
