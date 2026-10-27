"""The editor panel is in Polish: Django's own catalogue plus ours, in `backend/locale/pl/`."""

import ast
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils.translation import gettext, ngettext

from archive.tests.factories import WorkFactory

CATALOGUE = Path(settings.LOCALE_PATHS[0]) / "pl" / "LC_MESSAGES" / "django.po"


def catalogue_entries() -> list[dict[str, str]]:
    """The entries of the Polish catalogue, header excluded, keyed by `msgid`, `msgstr[0]`…

    A `flags` key holds the entry's `#,` comment, e.g. "fuzzy, python-format".
    """
    entries = []
    for block in CATALOGUE.read_text(encoding="utf-8").strip().split("\n\n"):
        entry: dict[str, str] = {"flags": ""}
        keyword = ""
        for line in block.splitlines():
            if line.startswith("#,"):
                entry["flags"] = line[2:].strip()
            elif line.startswith("#"):
                continue
            elif match := re.fullmatch(r"(msgid|msgid_plural|msgstr(?:\[\d\])?) (\".*\")", line):
                keyword = match.group(1)
                entry[keyword] = ast.literal_eval(match.group(2))
            else:
                entry[keyword] += ast.literal_eval(line)
        if entry["msgid"]:
            entries.append(entry)
    return entries


class TestCatalogue:
    def test_every_message_is_translated(self) -> None:
        # Arrange
        entries = catalogue_entries()

        # Act
        untranslated = [
            entry["msgid"]
            for entry in entries
            if "fuzzy" in entry["flags"]
            or not all(value for key, value in entry.items() if key.startswith("msgstr"))
        ]

        # Assert
        assert entries
        assert untranslated == []

    def test_compiled_catalogue_matches_the_source(self) -> None:
        """Catches a `django.po` edited without running `make messages` to compile it."""
        # Arrange
        entries = catalogue_entries()

        # Act
        stale = [
            entry["msgid"]
            for entry in entries
            if (
                [ngettext(entry["msgid"], entry["msgid_plural"], n) for n in (1, 2, 5)]
                != [entry["msgstr[0]"], entry["msgstr[1]"], entry["msgstr[2]"]]
                if "msgid_plural" in entry
                else gettext(entry["msgid"]) != entry["msgstr"]
            )
        ]

        # Assert
        assert stale == []


@pytest.mark.django_db
class TestEditorPanelLanguage:
    def test_menu_names_every_entity_in_polish(self, admin_client: Client) -> None:
        # Act
        response = admin_client.get(reverse("admin:index"))

        # Assert
        content = response.content.decode()
        assert '<html lang="pl"' in content
        for name in (
            "Archiwum",
            "Utwory",
            "Maszynopisy",
            "Zapiski",
            "Teksty sekundarne",
            "Materiały kontekstowe",
            "Tagi",
            "Fragmenty",
            "Instytucje",
            "Treści serwisu",
            "Członkowie zespołu",
            "Wyloguj się",
        ):
            assert name in content

    def test_work_form_labels_and_choices_are_polish(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        response = admin_client.get(reverse("admin:archive_work_change", args=[work.pk]))

        # Assert
        content = response.content.decode()
        for text in ("Tytuł", "Gatunek", "Okładka", "Szkic", "Opublikowany", "Wydania", "Zapisz"):
            assert text in content
