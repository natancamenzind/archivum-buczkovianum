"""US-RA-06: every item on the work page opens its own page (R-01)."""

from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

import pytest
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import Settings

from archive.models import ContentKind, Status, Work
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

PUBLISHED = Status.PUBLISHED


@pytest.fixture(autouse=True)
def built_site(settings: Settings, tmp_path: Path) -> None:
    """The built React app that Django serves for every page, and a place for uploads."""
    (tmp_path / "index.html").write_text("<title></title>", encoding="utf-8")
    settings.FRONTEND_DIST_DIR = tmp_path
    settings.MEDIA_ROOT = tmp_path / "media"


def work_page_links(client: Client, work: Work) -> list[str]:
    """The links `frontend/src/pages/WorkPage.tsx` builds from the work's endpoint to archive
    pages: the main column, the tag column and the contextual materials block. Editions have no
    page; links inside descriptions are the editors' own."""
    response = client.get(reverse("work", args=[work.slug]))
    assert response.status_code == 200
    page: dict[str, Any] = response.json()
    fragments = page["fragments"]["items"]
    notes = page["notes"]
    materials = page["materials"]["texts"] + page["materials"]["visuals"]
    chips = [tag for card in fragments + notes for tag in card["tags"]]
    links = [item["url"] for item in fragments + notes + materials]
    links += [f"/typescripts/{typescript['id']}" for typescript in page["typescripts"]]
    links += [f"/tags/{tag['slug']}" for tag in page["tags"] + chips]
    if page["main_typescript"] is not None and len(fragments) < page["fragments"]["total"]:
        links.append(f"/typescripts/{page['main_typescript']}?fragments=all")
    return links


def assert_opens_a_page(client: Client, link: str) -> None:
    """The site serves the link's page, the page's endpoint finds its entity, and a
    `?fragment=` is in the text that page reads."""
    url = urlsplit(link)
    assert client.get(link).status_code == 200, link
    response = client.get(f"/api{url.path}/")
    assert response.status_code == 200, link
    for fragment in parse_qs(url.query).get("fragment", []):
        text = client.get(reverse("document", args=[response.json()["document"]]))
        assert text.status_code == 200, link
        assert int(fragment) in [item["id"] for item in text.json()["fragments"]], link


@pytest.mark.django_db
class TestDrillDown:
    def test_us_ra_06_ac1_every_item_on_the_demo_work_pages_opens_its_page(
        self, client: Client
    ) -> None:
        # Arrange
        call_command("load_demo_data", stdout=StringIO())

        # Act
        links = [
            link for work in Work.objects.published() for link in work_page_links(client, work)
        ]

        # Assert: the demo has a link to every kind of page the work page links to.
        for link in links:
            assert_opens_a_page(client, link)
        assert {urlsplit(link).path.split("/")[1] for link in links} == {
            "typescripts",
            "notes",
            "tags",
            "secondary-texts",
            "materials",
        }
        assert any("?fragment=" in link for link in links)
        assert any("?fragments=all" in link for link in links)

    def test_us_ra_06_ac1_items_linked_next_to_drafts_open_their_pages(
        self, client: Client
    ) -> None:
        # Arrange: one published item of each kind, each beside a draft, all carrying tags.
        work = WorkFactory.create(status=PUBLISHED)
        EditionFactory.create(work=work)
        tag = TagFactory.create(status=PUBLISHED)
        draft_tag = TagFactory.create(status=Status.DRAFT)
        document = DocumentFactory.create(ocr=True, text="Pierwsza strona.", page_offsets=[0])
        TypescriptFactory.create(work=work, is_main=True, status=PUBLISHED, document=document)
        FragmentFactory.create(document=document).tags.add(tag, draft_tag)
        TypescriptFactory.create(work=work, status=Status.DRAFT)
        for status in (PUBLISHED, Status.DRAFT):
            note = NoteFactory.create(status=status)
            note.works.add(work)
            note.tags.add(tag, draft_tag)
            SecondaryTextWorkLinkFactory.create(
                work=work, secondary_text=SecondaryTextFactory.create(status=status)
            ).tags.add(tag, draft_tag)
            MaterialWorkLinkFactory.create(
                work=work, material=ContextualMaterialFactory.create(status=status)
            )
            photo = ContextualMaterialFactory.create(
                status=status,
                content_kind=ContentKind.IMAGE,
                external_url="",
                image=ContentFile(b"image", name="photo.jpg"),
                image_alt="Autor przy biurku",
            )
            MaterialWorkLinkFactory.create(work=work, material=photo).tags.add(tag)

        # Act
        links = work_page_links(client, work)

        # Assert: a fragment and its tag chip, a typescript, a note and its tag chip, the tag
        # column's tag, a secondary text and two materials.
        for link in links:
            assert_opens_a_page(client, link)
        assert len(links) == 9
