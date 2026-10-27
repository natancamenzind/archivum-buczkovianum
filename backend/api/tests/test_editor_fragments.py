from typing import Any

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from archive.models import ContentKind, Status, Tag
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    NoteFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)
from search.models import EntityType
from search.tests.test_index import entry, stored

API_URL = reverse("editor-fragments")
PUBLISHED = Status.PUBLISHED


@pytest.fixture
def staff_client(client: Client) -> Client:
    user = User.objects.create_user(username="editor", password="secret", is_staff=True)
    client.force_login(user)
    return client


def create_fragment(client: Client, **payload: Any) -> dict[str, Any]:
    response = client.post(API_URL, payload, content_type="application/json")
    assert response.status_code == 201
    result: dict[str, Any] = response.json()
    return result


@pytest.mark.django_db
class TestEditorFragmentsApi:
    def test_us_wr_09_ac2_anonymous_requests_are_rejected(self, client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None

        # Act
        response = client.post(
            API_URL,
            {
                "document": document.pk,
                "start": 0,
                "end": 6,
                "quote": "Czarny",
                "tag_ids": [TagFactory.create().pk],
            },
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 403

    def test_us_wr_09_ac1_non_main_typescript_cannot_be_tagged(self, staff_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        typescript = TypescriptFactory.create(work=work, is_main=False)
        document = typescript.document
        assert document is not None

        # Act
        response = staff_client.post(
            API_URL,
            {
                "document": document.pk,
                "start": 0,
                "end": 6,
                "quote": "Czarny",
                "tag_ids": [TagFactory.create().pk],
            },
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 400

    def test_us_wr_09_ac2_staff_creates_a_fragment_with_tags(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True, status=PUBLISHED)
        document = typescript.document
        assert document is not None
        tag = TagFactory.create(status=PUBLISHED, title="Dezerter")

        # Act
        result = create_fragment(
            staff_client,
            document=document.pk,
            start=0,
            end=6,
            quote="Czarny",
            tag_ids=[tag.pk],
        )

        # Assert
        assert result["quote"] == "Czarny"
        assert [item["title"] for item in result["tags"]] == ["Dezerter"]
        indexed = stored(EntityType.FRAGMENT, result["id"])
        assert indexed is not None
        assert stored(EntityType.TAG, tag.pk) is not None

    def test_us_wr_09_ac3_overlapping_fragments_are_allowed(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None
        tag_one = TagFactory.create()
        tag_two = TagFactory.create()
        create_fragment(
            staff_client,
            document=document.pk,
            start=0,
            end=12,
            quote="Czarny potok",
            tag_ids=[tag_one.pk],
        )

        # Act
        second = create_fragment(
            staff_client,
            document=document.pk,
            start=7,
            end=19,
            quote="potok płynie",
            tag_ids=[tag_two.pk],
        )

        # Assert
        assert document.fragments.count() == 2
        assert second["start"] == 7

    def test_us_wr_09_ac2_selection_must_lie_within_the_text(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None
        text_len = len(document.text)

        # Act
        response = staff_client.post(
            API_URL,
            {
                "document": document.pk,
                "start": 0,
                "end": text_len + 1,
                "quote": document.text,
                "tag_ids": [TagFactory.create().pk],
            },
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 400

    def test_us_wr_09_ac2_quote_must_match_the_selection(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True)
        document = typescript.document
        assert document is not None

        # Act
        response = staff_client.post(
            API_URL,
            {
                "document": document.pk,
                "start": 0,
                "end": 6,
                "quote": "wrong",
                "tag_ids": [TagFactory.create().pk],
            },
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 400

    def test_us_wr_09_ac1_note_with_text_can_be_tagged(self, staff_client: Client) -> None:
        # Arrange
        note = NoteFactory.create(
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(text="Zapisek."),
        )
        tag = TagFactory.create()

        # Act
        result = create_fragment(
            staff_client,
            document=note.document_id,
            start=0,
            end=7,
            quote="Zapisek",
            tag_ids=[tag.pk],
        )

        # Assert
        assert result["document"] == note.document_id

    def test_patch_updates_tags_and_reindexes(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(is_main=True, status=PUBLISHED)
        document = typescript.document
        assert document is not None
        fragment = FragmentFactory.create(document=document, start=0, end=6, quote="Czarny")
        old_tag = TagFactory.create(status=PUBLISHED, title="Old")
        new_tag = TagFactory.create(status=PUBLISHED, title="New")
        fragment.tags.add(old_tag)
        fragment.update_search_entry()
        Tag.update_search_entries()

        # Act
        response = staff_client.patch(
            reverse("editor-fragment", args=[fragment.pk]),
            {"tag_ids": [new_tag.pk]},
            content_type="application/json",
        )

        # Assert
        assert response.status_code == 200
        fragment.refresh_from_db()
        assert list(fragment.tags.values_list("title", flat=True)) == ["New"]
        assert entry(EntityType.FRAGMENT, fragment.pk) is not None

    def test_delete_removes_the_fragment(self, staff_client: Client) -> None:
        # Arrange
        fragment = FragmentFactory.create(document=TypescriptFactory.create(is_main=True).document)

        # Act
        response = staff_client.delete(reverse("editor-fragment", args=[fragment.pk]))

        # Assert
        assert response.status_code == 204
        assert not fragment.__class__.objects.filter(pk=fragment.pk).exists()
