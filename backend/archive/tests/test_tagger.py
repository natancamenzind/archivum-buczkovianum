import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import Client, RequestFactory
from django.urls import reverse

from archive.models import ContentKind, Fragment
from archive.tagger import highlight_segments
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    NoteFactory,
    TypescriptFactory,
    WorkFactory,
)


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
        for name in ("location", "shelfmark", "description", "is_featured"):
            assert name in fields


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
