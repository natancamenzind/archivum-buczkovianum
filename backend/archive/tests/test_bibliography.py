"""A work's bibliography in the editor panel (US-WR-15)."""

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from archive.models import Status, Work
from archive.tests.factories import BibliographyEntryFactory, WorkFactory


def change_url(work: Work) -> str:
    return reverse("admin:archive_work_change", args=[work.pk])


def form_data(work: Work, *entries: dict[str, Any]) -> dict[str, Any]:
    """What the work's change form posts: its fields as they are and the bibliography inline."""
    data: dict[str, Any] = {
        "title": work.title,
        "slug": work.slug,
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
            {"text": "Jan Błoński, Wertepy, Twórczość, Warszawa 1948, s. 3"},
            {"text": "Jerzy Kwiatkowski, Klucze do wyobraźni, PIW, Warszawa 1964"},
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
        kept = BibliographyEntryFactory.create(work=work, text="Stary opis")
        removed = BibliographyEntryFactory.create(work=work)
        data = form_data(
            work,
            {"id": kept.pk, "work": work.pk, "text": "Nowy opis"},
            {"id": removed.pk, "work": work.pk, "text": removed.text, "DELETE": "on"},
        )

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 302
        assert texts(work) == ["Nowy opis"]

    def test_us_wr_15_ac1_an_entry_needs_its_text(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        entry = BibliographyEntryFactory.create(work=work, text="Stary opis")
        data = form_data(work, {"id": entry.pk, "work": work.pk, "text": ""})

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 200
        assert texts(work) == ["Stary opis"]

    def test_us_wr_15_ac1_an_entry_is_one_line(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()
        data = form_data(work, {"text": "Pierwsza linia\r\ndruga linia"})

        # Act
        response = admin_client.post(change_url(work), data)

        # Assert
        assert response.status_code == 302
        assert texts(work) == ["Pierwsza linia druga linia"]

    def test_us_wr_15_ac2_entries_are_in_polish_alphabetical_order(self) -> None:
        # Arrange
        work = WorkFactory.create()
        for text in ("Żukrowski", "Zarycki", "Łempicki", "Lisowski", "Śliwiński", "Sandauer"):
            BibliographyEntryFactory.create(work=work, text=text)
        BibliographyEntryFactory.create(work=work, text="abramowicz")
        BibliographyEntryFactory.create(work=work, text="Błoński")

        # Act
        result = texts(work)

        # Assert
        assert result == [
            "abramowicz",
            "Błoński",
            "Lisowski",
            "Łempicki",
            "Sandauer",
            "Śliwiński",
            "Zarycki",
            "Żukrowski",
        ]

    def test_us_wr_15_ac2_equal_entries_keep_the_order_they_were_added_in(self) -> None:
        # Arrange
        work = WorkFactory.create()
        first, second = (BibliographyEntryFactory.create(work=work, text="Błoński") for _ in "ab")

        # Act
        result = list(work.bibliography.all())

        # Assert
        assert result == [first, second]

    def test_us_wr_15_ac2_editors_do_not_set_the_order(self, admin_client: Client) -> None:
        # Act
        response = admin_client.get(reverse("admin:archive_work_add"))

        # Assert
        _editions, bibliography = response.context["inline_admin_formsets"]
        assert list(bibliography.formset.form.base_fields) == ["text"]
