import html
import re

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import reverse

from archive.models import ContentKind, Fragment
from archive.tagger import highlight_segments, tagger_pages
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    InstitutionFactory,
    NoteFactory,
    TypescriptFactory,
    WorkFactory,
)


def shown_text(content: str) -> str:
    """The text the tagger shows: its pages' text, without page numbers or highlight markup."""
    pages = re.findall(r'<div class="tagger-page-text"[^>]*>(.*?)</div>', content, re.DOTALL)
    return "".join(html.unescape(re.sub(r"<[^>]+>", "", page)) for page in pages)


@pytest.mark.django_db
class TestTaggerEligibility:
    def test_us_wr_09_ac1_main_typescript_offers_tagger(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None

        # Act
        offers = document.offers_tagger()

        # Assert
        assert offers is True

    def test_us_wr_09_ac1_non_main_typescript_does_not(self) -> None:
        # Arrange
        work = WorkFactory.create()
        typescript = TypescriptFactory.create(work=work, is_main=False)
        document = typescript.document
        assert document is not None

        # Act
        offers = document.offers_tagger()

        # Assert
        assert offers is False

    def test_us_wr_09_ac1_note_with_text_offers_tagger(self) -> None:
        # Arrange
        note = NoteFactory.create(
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(),
        )

        document = note.document
        assert document is not None

        # Act
        offers = document.offers_tagger()

        # Assert
        assert offers is True


@pytest.mark.django_db
class TestTaggerAdmin:
    def test_us_wr_09_ac1_tagger_link_on_main_typescript(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)

        # Act
        change_url = reverse("admin:archive_typescript_change", args=[typescript.pk])
        response = admin_client.get(change_url)

        # Assert
        tagger_url = reverse("admin:archive_document_tagger", args=[typescript.document_id])
        assert tagger_url in response.content.decode()

    def test_us_wr_09_ac1_no_tagger_link_on_secondary_typescript(
        self, admin_client: Client
    ) -> None:
        # Arrange
        work = WorkFactory.create()
        typescript = TypescriptFactory.create(work=work, is_main=False)

        # Act
        change_url = reverse("admin:archive_typescript_change", args=[typescript.pk])
        response = admin_client.get(change_url)

        # Assert
        tagger_url = reverse("admin:archive_document_tagger", args=[typescript.document_id])
        assert tagger_url not in response.content.decode()

    def test_tagger_view_lists_fragments_needing_review_first(self, admin_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None
        fine = FragmentFactory.create(document=document, start=0, end=6, quote="Czarny")
        flagged = FragmentFactory.create(
            document=document, start=7, end=12, quote="potok", needs_review=True
        )
        url = reverse("admin:archive_document_tagger", args=[document.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        assert response.context["fragments"][0] == flagged
        assert response.context["fragments"][1] == fine

    @pytest.mark.parametrize("fragments", [[], [(7, 12)], [(0, 6), (7, 20)]])
    def test_us_wr_09_ac2_tagger_shows_the_text_exactly_as_stored(
        self, admin_client: Client, fragments: list[tuple[int, int]]
    ) -> None:
        # Arrange: the script counts a selection's offsets over the shown text, so the template
        # must add nothing to it, not even its own indentation.
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None
        document.text = "Czarny potok.\nPłynie przez las.\n"
        document.save()
        for start, end in fragments:
            FragmentFactory.create(document=document, start=start, end=end)
        url = reverse("admin:archive_document_tagger", args=[document.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        assert shown_text(response.content.decode()) == document.text

    def test_arc_61_tagger_splits_the_text_into_the_readers_pages(
        self, admin_client: Client
    ) -> None:
        # Arrange: a fragment runs from the first scan page onto the second.
        document = DocumentFactory.create(
            ocr=True, text="Czarny potok.\nPłynie przez las.\n", page_offsets=[0, 14, 32]
        )
        TypescriptFactory.create(document=document, is_main=True)
        FragmentFactory.create(document=document, start=7, end=20)
        url = reverse("admin:archive_document_tagger", args=[document.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        content = response.content.decode()
        pages = re.findall(
            r'<section class="tagger-page" id="tagger-page-(\d+)">.*?'
            r'<div class="tagger-page-text" data-start="(\d+)">(.*?)</div>',
            content,
            re.DOTALL,
        )
        assert [(number, start) for number, start, _ in pages] == [
            ("1", "0"),
            ("2", "14"),
            ("3", "32"),
        ]
        assert [html.unescape(re.sub(r"<[^>]+>", "", text)) for _, _, text in pages] == [
            "Czarny potok.\n",
            "Płynie przez las.\n",
            "",
        ]
        assert shown_text(content) == document.text
        assert "Strona 2" in content

    def test_arc_61_tagger_offers_to_go_to_a_page(self, admin_client: Client) -> None:
        # Arrange
        document = DocumentFactory.create(ocr=True, text="a" * 30, page_offsets=[0, 10, 20])
        TypescriptFactory.create(document=document, is_main=True)
        url = reverse("admin:archive_document_tagger", args=[document.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        content = response.content.decode()
        assert 'id="tagger-go-to-page"' in content
        assert 'min="1" max="3"' in content
        assert "z 3 stron" in content

    def test_arc_61_plain_text_has_no_pages(self, admin_client: Client) -> None:
        # Arrange
        note = NoteFactory.create(
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(text="Czarny potok."),
        )
        url = reverse("admin:archive_document_tagger", args=[note.document_id])

        # Act
        response = admin_client.get(url)

        # Assert
        content = response.content.decode()
        assert shown_text(content) == "Czarny potok."
        assert "tagger-go-to-page" not in content
        assert "tagger-page-number" not in content

    def test_us_wr_09_ac6_fragment_form_has_metadata_fields(
        self, rf: RequestFactory, admin_user: User
    ) -> None:
        # Arrange
        model_admin = admin.site.get_model_admin(Fragment)
        request = rf.get("/")
        request.user = admin_user

        # Act
        fields = model_admin.get_fields(request)

        # Assert
        for name in ("shelfmark", "is_featured"):
            assert name in fields
        for name in ("unit_number", "scan_number", "description"):
            assert name not in fields
        assert "shelfmark" in model_admin.get_readonly_fields(request)

    def test_arc_11_fragment_form_shows_the_shelfmark_with_its_scan_page(
        self, admin_client: Client
    ) -> None:
        # Arrange
        document = DocumentFactory.create(ocr=True, text="a" * 30, page_offsets=list(range(20)))
        TypescriptFactory.create(
            document=document, institution=InstitutionFactory.create(), shelfmark="1618"
        )
        fragment = FragmentFactory.create(document=document, start=18, end=25)

        # Act
        response = admin_client.get(reverse("admin:archive_fragment_change", args=[fragment.pk]))

        # Assert
        assert "ML, sygn. 1618.19" in response.content.decode()

    def test_arc_11_fragment_list_shows_the_shelfmark_with_its_scan_page(
        self, admin_client: Client
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(
            institution=InstitutionFactory.create(), shelfmark="1618"
        )
        FragmentFactory.create(document=typescript.document)

        # Act
        response = admin_client.get(reverse("admin:archive_fragment_changelist"))

        # Assert
        assert "ML, sygn. 1618.1" in response.content.decode()


@pytest.mark.django_db
class TestHighlightSegments:
    def test_us_wr_09_ac3_overlapping_fragments_share_a_segment(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok płynie.")
        first = FragmentFactory.create(document=document, start=0, end=12)
        second = FragmentFactory.create(document=document, start=7, end=19)

        # Act
        segments = highlight_segments(document.text, [first, second])

        # Assert
        shared = [segment for segment in segments if len(segment.fragment_ids) == 2]
        assert shared
        assert shared[0].text == "potok"

    def test_arc_61_a_fragment_across_pages_is_highlighted_on_each(self) -> None:
        # Arrange
        document = DocumentFactory.create(
            ocr=True, text="Czarny potok.\nPłynie przez las.\n", page_offsets=[0, 14]
        )
        fragment = FragmentFactory.create(document=document, start=7, end=20)

        # Act
        pages = tagger_pages(document, [fragment])

        # Assert
        highlighted = [
            [segment.text for segment in page.segments if segment.fragment_ids] for page in pages
        ]
        assert highlighted == [["potok.\n"], ["Płynie"]]
        assert [page.start for page in pages] == [0, 14]
