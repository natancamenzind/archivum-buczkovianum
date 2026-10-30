"""`manage.py load_demo_data`: the sample archive of design/rules.md (docs/plan.md, step 5)."""

import re
from collections.abc import Iterator
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import transaction
from django.test import override_settings
from pytest_django import DjangoDbBlocker
from pytest_django.fixtures import Settings

from archive.management.commands import load_demo_data
from archive.management.commands.load_demo_data import spread_sentences
from archive.models import (
    Document,
    Fragment,
    Institution,
    Status,
    Tag,
    TeamMember,
    Typescript,
    Work,
)
from archive.tests.factories import (
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextWorkLinkFactory,
    SiteSettingsFactory,
    TagFactory,
    TeamMemberFactory,
    TypescriptFactory,
)
from search.models import SearchEntry


def index() -> set[tuple[object, ...]]:
    """Every entry with what search, the filters and snippets use."""
    fields = ("entity_type", "entity_id", "url", "body", "work_ids", "decades", "has_scan")
    rows = SearchEntry.objects.values_list(*fields, "vector")
    return {tuple(tuple(v) if isinstance(v, list) else v for v in row) for row in rows}


@pytest.fixture(scope="class")
def loaded_demo(
    django_db_setup: None,
    django_db_blocker: DjangoDbBlocker,
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[tuple[str, Path]]:
    """Loads the demo once per class (~3 s), in a transaction each test's own one nests in."""
    media = tmp_path_factory.mktemp("media")
    with django_db_blocker.unblock(), override_settings(MEDIA_ROOT=media), transaction.atomic():
        output = StringIO()
        call_command("load_demo_data", stdout=output)
        yield output.getvalue(), media
        transaction.set_rollback(True)


@pytest.fixture
def demo(loaded_demo: tuple[str, Path], settings: Settings) -> str:
    output, settings.MEDIA_ROOT = loaded_demo
    return output


@pytest.mark.django_db
@pytest.mark.xdist_group("loaded_demo")
class TestLoadedDemoData:
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


@pytest.mark.django_db
class TestDemoData:
    def test_replaces_the_content_and_keeps_the_users(self, admin_user: User) -> None:
        # Arrange
        MaterialWorkLinkFactory.create()
        SecondaryTextWorkLinkFactory.create()
        note = NoteFactory.create(institution=InstitutionFactory.create(abbreviation="BN"))
        note.tags.add(TagFactory.create(status=Status.PUBLISHED))
        typescript = TypescriptFactory.create(status=Status.PUBLISHED)
        EditionFactory.create(work=typescript.work)
        FragmentFactory.create(document=typescript.document)
        TeamMemberFactory.create()
        SiteSettingsFactory.create()

        # Act
        output = StringIO()
        call_command("load_demo_data", stdout=output)

        # Assert
        assert output.getvalue() == "Loaded 4 works, 62 fragments and 12 tags.\n"
        assert Institution.objects.get().abbreviation == "ML"
        assert TeamMember.objects.count() == len(TeamMember.Group)
        assert not SearchEntry.objects.filter(title__in=(note.title, typescript.title)).exists()
        assert User.objects.get() == admin_user

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
