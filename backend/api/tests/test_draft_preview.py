from collections.abc import Callable

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from archive.models import ContentKind, Publishable, Status
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

DRAFT = Status.DRAFT
PUBLISHED = Status.PUBLISHED


def page_url(entity: Publishable) -> str:
    """The entity's page endpoint: `/api` and its site URL."""
    return f"/api{entity.get_absolute_url()}/"


# Every entity page endpoint (architecture section 7), by its entity's factory.
ENTITIES: dict[str, Callable[[Status], Publishable]] = {
    "work": lambda status: WorkFactory.create(status=status),
    "tag": lambda status: TagFactory.create(status=status),
    "typescript": lambda status: TypescriptFactory.create(status=status),
    "note": lambda status: NoteFactory.create(status=status),
    "secondary text": lambda status: SecondaryTextFactory.create(status=status),
    "material": lambda status: ContextualMaterialFactory.create(status=status),
}


@pytest.fixture
def staff_client(client: Client) -> Client:
    client.force_login(User.objects.create_user(username="editor", is_staff=True))
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("kind", ENTITIES)
class TestDraftPreview:
    def test_us_wr_13_ac2_staff_sees_a_draft_marked_as_a_draft(
        self, staff_client: Client, kind: str
    ) -> None:
        # Arrange
        entity = ENTITIES[kind](DRAFT)

        # Act
        response = staff_client.get(page_url(entity))

        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == entity.title
        assert response.json()["is_draft"] is True

    def test_us_wr_13_ac2_anonymous_readers_get_404_for_a_draft(
        self, client: Client, kind: str
    ) -> None:
        # Arrange
        entity = ENTITIES[kind](DRAFT)

        # Act
        response = client.get(page_url(entity))

        # Assert
        assert response.status_code == 404

    def test_us_wr_13_ac2_a_reader_who_is_not_staff_gets_404_for_a_draft(
        self, client: Client, kind: str
    ) -> None:
        # Arrange
        entity = ENTITIES[kind](DRAFT)
        client.force_login(User.objects.create_user(username="reader"))

        # Act
        response = client.get(page_url(entity))

        # Assert
        assert response.status_code == 404

    def test_us_wr_13_ac2_a_published_entity_is_not_a_draft(
        self, staff_client: Client, kind: str
    ) -> None:
        # Arrange
        entity = ENTITIES[kind](PUBLISHED)

        # Act
        response = staff_client.get(page_url(entity))

        # Assert
        assert response.status_code == 200
        assert response.json()["is_draft"] is False


@pytest.mark.django_db
class TestDraftText:
    def test_us_wr_13_ac2_staff_reads_the_text_of_a_draft(self, staff_client: Client) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=DRAFT)

        # Act
        response = staff_client.get(reverse("document", args=[typescript.document_id]))

        # Assert
        assert response.status_code == 200
        assert response.json()["is_draft"] is True

    def test_us_wr_13_ac2_anonymous_readers_get_404_for_the_text_of_a_draft(
        self, client: Client
    ) -> None:
        # Arrange
        note = NoteFactory.create(
            status=DRAFT,
            content_kind=ContentKind.PLAIN_TEXT,
            external_url="",
            document=DocumentFactory.create(),
        )

        # Act
        response = client.get(reverse("document", args=[note.document_id]))

        # Assert
        assert response.status_code == 404

    def test_us_wr_13_ac2_the_text_of_a_published_item_is_not_a_draft(
        self, staff_client: Client
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=PUBLISHED)

        # Act
        response = staff_client.get(reverse("document", args=[typescript.document_id]))

        # Assert
        assert response.json()["is_draft"] is False


@pytest.mark.django_db
class TestDraftsStayUnlisted:
    def test_r_06_a_draft_preview_lists_no_other_drafts(self, staff_client: Client) -> None:
        # Arrange
        published = WorkFactory.create(status=PUBLISHED)
        note = NoteFactory.create(status=DRAFT)
        note.works.add(published, WorkFactory.create(status=DRAFT))
        note.tags.add(TagFactory.create(status=DRAFT))

        # Act
        result = staff_client.get(page_url(note)).json()

        # Assert
        assert [work["slug"] for work in result["works"]] == [published.slug]
        assert result["tags"] == []

    @pytest.mark.parametrize(
        ("factory", "link_factory", "item_field"),
        (
            (SecondaryTextFactory, SecondaryTextWorkLinkFactory, "secondary_text"),
            (ContextualMaterialFactory, MaterialWorkLinkFactory, "material"),
        ),
    )
    def test_us_wr_13_ac2_a_draft_preview_shows_its_work_link_tags(
        self,
        staff_client: Client,
        factory: type[SecondaryTextFactory | ContextualMaterialFactory],
        link_factory: type[SecondaryTextWorkLinkFactory | MaterialWorkLinkFactory],
        item_field: str,
    ) -> None:
        # Arrange
        item = factory.create(status=DRAFT)
        wojna = TagFactory.create(title="Wojna", slug="wojna", status=PUBLISHED)
        link_factory.create(
            **{item_field: item, "work": WorkFactory.create(status=PUBLISHED)}
        ).tags.add(wojna)
        link_factory.create(
            **{item_field: item, "work": WorkFactory.create(status=DRAFT)}
        ).tags.add(TagFactory.create(status=PUBLISHED))

        # Act
        result = staff_client.get(page_url(item)).json()

        # Assert: as the page will be once published; a link to a draft work brings none.
        assert result["tags"] == [{"slug": "wojna", "title": "Wojna"}]

    def test_r_06_a_draft_preview_leaves_out_draft_typescripts_and_related_tags(
        self, staff_client: Client
    ) -> None:
        # Arrange
        typescript = TypescriptFactory.create(status=DRAFT)
        TypescriptFactory.create(status=DRAFT, work=typescript.work)
        tag = TagFactory.create(status=DRAFT)
        tag.related.add(TagFactory.create(status=DRAFT))

        # Act
        typescript_page = staff_client.get(page_url(typescript)).json()
        tag_page = staff_client.get(page_url(tag)).json()

        # Assert: only the previewed draft itself is shown.
        assert [row["id"] for row in typescript_page["work_typescripts"]] == []
        assert tag_page["related"] == []

    def test_r_06_staff_sees_no_draft_in_lists_or_search(self, staff_client: Client) -> None:
        # Arrange
        WorkFactory.create(status=DRAFT, title="Szkicownik")

        # Act
        listed = staff_client.get(reverse("works")).json()
        found = staff_client.get(reverse("search"), {"q": "Szkicownik"}).json()

        # Assert
        assert listed == []
        assert found["works"] == []

    def test_r_06_staff_sees_no_draft_on_a_published_page(self, staff_client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=PUBLISHED)
        NoteFactory.create(status=DRAFT).works.add(work)
        TypescriptFactory.create(status=DRAFT, work=work)

        # Act
        result = staff_client.get(page_url(work)).json()

        # Assert
        assert result["notes"] == []
        assert result["typescripts"] == []
