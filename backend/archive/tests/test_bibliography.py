"""A work's bibliography in the editor panel (US-WR-15)."""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from archive.models import BibliographyEntry, Status, Work
from archive.tests.factories import BibliographyEntryFactory, WorkFactory


def change_url(work: Work) -> str:
    return reverse("admin:archive_work_change", args=[work.pk])


def form_data(work: Work, *entries: dict[str, Any]) -> dict[str, Any]:
    """What the work's change form posts: its fields as they are and the bibliography inline."""
    data: dict[str, Any] = {
        "title": work.title,
        "slug": work.slug,
        "genre": work.genre,
        "status": work.status,
        "description": work.description,
        "editions-TOTAL_FORMS": 0,
        "editions-INITIAL_FORMS": 0,
        "bibliography-TOTAL_FORMS": len(entries),
        "bibliography-INITIAL_FORMS": sum("id" in entry for entry in entries),
    }
    for index, entry in enumerate(entries):
        for name, value in entry.items():
            data[f"bibliography-{index}-{name}"] = value
    return data


def texts(work: Work) -> list[str]:
    return list(work.bibliography.values_list("text", flat=True))


@pytest.mark.django_db
class TestBibliographyInThePanel:
    def test_us_wr_15_ac1_adds_entries_inline_on_the_work(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create(status=Status.PUBLISHED)
        data = form_data(
            work,
            {"text": "Jan Błoński, Wertepy, Twórczość, Warszawa 1948, s. 3", "order": 1},
            {"text": "Jerzy Kwiatkowski, Klucze do wyobraźni, PIW, Warszawa 1964", "order": 2},
        )

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 302
        assert texts(work) == [
            "Jan Błoński, Wertepy, Twórczość, Warszawa 1948, s. 3",
            "Jerzy Kwiatkowski, Klucze do wyobraźni, PIW, Warszawa 1964",
        ]

    def test_us_wr_15_ac1_edits_and_deletes_entries(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        kept = BibliographyEntryFactory.create(work=work, text="Stary opis", order=1)
        removed = BibliographyEntryFactory.create(work=work, order=2)
        data = form_data(
            work,
            {"id": kept.pk, "work": work.pk, "text": "Nowy opis", "order": 1},
            {"id": removed.pk, "work": work.pk, "text": removed.text, "order": 2, "DELETE": "on"},
        )

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 302
        assert texts(work) == ["Nowy opis"]

    def test_us_wr_15_ac1_an_entry_needs_its_text(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.post(change_url(work), form_data(work, {"text": "", "order": 1}))

        # Assert
        assert response.status_code == 200
        assert not BibliographyEntry.objects.exists()

    def test_us_wr_15_ac1_an_entry_is_one_line(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, {"text": "Pierwsza linia\r\ndruga linia", "order": 1})

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 302
        assert texts(work) == ["Pierwsza linia druga linia"]

    def test_us_wr_15_ac2_lower_numbers_come_first(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(
            work,
            {"text": "Trzecia", "order": 30},
            {"text": "Pierwsza", "order": 10},
            {"text": "Druga", "order": 20},
        )

        # Act
        admin_client.post(change_url(work), data)

        # Assert
        assert texts(work) == ["Pierwsza", "Druga", "Trzecia"]

    def test_us_wr_15_ac2_equal_numbers_keep_the_order_they_were_added_in(self) -> None:
        # Arrange
        work = WorkFactory.create()
        for text in ("Pierwsza", "Druga", "Trzecia"):
            BibliographyEntryFactory.create(work=work, text=text, order=0)

        # Act
        result = texts(work)

        # Assert
        assert result == ["Pierwsza", "Druga", "Trzecia"]
