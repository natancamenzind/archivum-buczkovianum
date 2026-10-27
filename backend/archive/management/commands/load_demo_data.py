"""Load the sample archive of design/rules.md ("Dane przykładowe"), to try the site by hand.

Everything goes through `full_clean()` and `save()`, so the search index is filled as it would be
by an editor. The scans and OCR texts in archive/demo/ are placeholders, not Buczkowski's texts.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction
from django.utils.text import slugify

from archive.models import (
    ContentKind,
    ContextualMaterial,
    Document,
    Edition,
    Fragment,
    Institution,
    MaterialWorkLink,
    Note,
    SecondaryText,
    SecondaryTextWorkLink,
    SiteSettings,
    Status,
    Tag,
    TeamMember,
    Typescript,
    Work,
)

DEMO_DIR = Path(__file__).resolve().parents[2] / "demo"
IMAGES_DIR = settings.BASE_DIR.parent / "design" / "assets" / "images"
COVER = "okladka-2f232c11.png"
PORTRAIT = "naglowek-strony-glownej-642bf583.jpg"
NOTE_SCAN = "obraz-skanu-6a63c23e.png"
PUBLISHED = Status.PUBLISHED
SENTENCE = re.compile(r"[^.!?\s][^.!?]*[.!?]")

# Tags and their occurrences, as in design/screens/lista-tagi.md.
TAGS = {
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


@dataclass
class TypescriptData:
    title: str
    shelfmark: str
    scan: str
    fragments: int = 0
    is_main: bool = False


@dataclass
class WorkData:
    slug: str
    title: str
    description: str
    editions: list[tuple[str, str, int]]
    typescripts: list[TypescriptData] = field(default_factory=list)


WORKS = [
    WorkData(
        "wertepy",
        "Wertepy",
        "Pierwsza powieść Leopolda Buczkowskiego, wydana w 1947 roku. Sceny z codziennego życia "
        "podolskiej wsi w dwudziestoleciu międzywojennym.",
        [
            ("Gebethner i Wolff", "Warszawa", 1947),
            ("Państwowy Instytut Wydawniczy", "Warszawa", 1957),
            ("Wydawnictwo Literackie", "Kraków", 1973),
        ],
        [
            TypescriptData("Pierwsza wersja", "1618", "wertepy-1618", 24, is_main=True),
            TypescriptData("Druga wersja", "1619", "wertepy-1619"),
        ],
    ),
    WorkData(
        "czarny-potok",
        "Czarny potok",
        "[Opis utworu: dwa, trzy zdania.]",
        [("Państwowy Instytut Wydawniczy", "Warszawa", 1954)],
        [TypescriptData("Maszynopis", "1609", "czarny-potok-1609", 18, is_main=True)],
    ),
    WorkData(
        "dorycki-kruzganek",
        "Dorycki krużganek",
        "[Opis utworu: dwa, trzy zdania.]",
        [("Państwowy Instytut Wydawniczy", "Warszawa", 1957)],
        [TypescriptData("Maszynopis", "1625", "dorycki-kruzganek-1625", 12, is_main=True)],
    ),
    WorkData(
        "pierwsza-swietnosc",
        "Pierwsza świetność",
        "[Opis utworu: dwa, trzy zdania.]",
        [("Państwowy Instytut Wydawniczy", "Warszawa", 1966)],
        [TypescriptData("Maszynopis", "1640", "pierwsza-swietnosc-1640", 8, is_main=True)],
    ),
]

# Fragments the design shows: (typescript shelfmark, number in the text) -> fields and tags.
SHOWN_FRAGMENTS: dict[tuple[str, int], dict[str, Any]] = {
    ("1618", 1): {
        "location": "rozdział I",
        "shelfmark": "1618.0009",
        "description": "Grzybniak leczy chorych podczas zimowej epidemii tyfusu w Dolinoszczęsnej.",
        "is_featured": True,
        "tags": ["Dezerter", "Epidemia"],
    },
    ("1618", 3): {
        "location": "rozdział III",
        "shelfmark": "1618.0019",
        "is_featured": True,
        "tags": ["Dezerter"],
    },
    ("1609", 2): {"shelfmark": "1609.0012", "tags": ["Dezerter"]},
}


def spread_sentences(text: str, count: int) -> list[re.Match[str]]:
    """`count` sentences spread evenly over the text, for fragments across all its pages.

    A sentence that starts with a lowercase letter, after any dash or quote, is skipped: it is
    the tail of a sentence cut by a page break, or a dialogue tag such as "- spytał.".
    """
    sentences = [s for s in SENTENCE.finditer(text) if not s.group().lstrip('-" ')[:1].islower()]
    if count > len(sentences):
        raise CommandError(f"The text has {len(sentences)} sentences, not {count}.")
    return [sentences[number * len(sentences) // count] for number in range(count)]


def image(name: str) -> ContentFile[bytes]:
    return ContentFile((IMAGES_DIR / name).read_bytes(), name=name)


def saved[M: models.Model](obj: M) -> M:
    """Validate and save, as the editor panel would."""
    obj.full_clean()
    obj.save()
    return obj


def ocr_document(name: str) -> Document:
    document = Document(kind=Document.Kind.OCR)
    document.scan.save(f"{name}.pdf", ContentFile((DEMO_DIR / f"{name}.pdf").read_bytes()), False)
    document.set_ocr_text((DEMO_DIR / f"{name}.txt").read_text(encoding="utf-8"))
    return saved(document)


class Command(BaseCommand):
    help = "Load the sample archive from design/rules.md into an empty database."

    def handle(self, *args: Any, **options: Any) -> None:
        if any(
            model.objects.exists() for model in (Work, Tag, Institution, TeamMember, SiteSettings)
        ):
            raise CommandError("The archive is not empty. Load the demo into an empty database.")
        if not IMAGES_DIR.is_dir():
            raise CommandError(f"The demo images come from the design export: {IMAGES_DIR}.")
        with transaction.atomic():
            self.load()
        self.stdout.write(
            f"Loaded {Work.objects.count()} works, {Fragment.objects.visible().count()} fragments "
            f"and {Tag.objects.published().count()} tags."
        )

    def load(self) -> None:
        institution = saved(Institution(abbreviation="ML", name="Muzeum Literatury"))
        tags = {
            name: saved(
                Tag(
                    title=name,
                    slug=slugify(name.replace("ł", "l")),
                    kind=Tag.Kind.KEYWORD,
                    status=PUBLISHED,
                )
            )
            for name in TAGS
        }
        saved(Tag(title="Brulion", slug="brulion", kind=Tag.Kind.INTERPRETATION))  # a draft
        works = {data.slug: self.load_work(data, institution, tags) for data in WORKS}

        # Whole items and a work link carry the rest of the design's occurrences.
        note = saved(
            Note(
                title="Notes 18 · karta 4",
                description="Notatka z notesu 18 o postaci dezertera.",
                institution=institution,
                shelfmark="1678.0104",
                content_kind=ContentKind.IMAGE,
                image=image(NOTE_SCAN),
                image_alt="Skan karty z notesu 18.",
                status=PUBLISHED,
            )
        )
        note.works.add(works["wertepy"])
        note.tags.add(tags["Dezerter"])
        letter = saved(
            SecondaryText(
                title="List nr 32",
                kind=SecondaryText.Kind.LETTER,
                description="Transkrypcja listu z zachowaniem układu oryginału.",
                author="Leopold Buczkowski",
                sender="Leopold Buczkowski",
                letter_date=date(1947, 10, 1),
                institution=institution,
                shelfmark="1701.0032",
                document=ocr_document("list-32-1701"),
                status=PUBLISHED,
            )
        )
        letter.tags.add(tags["Pamięć"])
        link = saved(SecondaryTextWorkLink(secondary_text=letter, work=works["wertepy"]))
        link.tags.add(tags["Pisanie"])
        review = saved(
            SecondaryText(
                title="[Tytuł recenzji]",
                kind=SecondaryText.Kind.REVIEW,
                author="[Autor recenzji]",
                source="[Wydawca, miejsce, rok, strony]",
                document=saved(Document(kind=Document.Kind.PLAIN, text="[Tekst recenzji.]")),
                status=PUBLISHED,
            )
        )
        saved(SecondaryTextWorkLink(secondary_text=review, work=works["wertepy"]))
        portrait = saved(
            ContextualMaterial(
                title="Portret Leopolda Buczkowskiego",
                content_kind=ContentKind.IMAGE,
                image=image(PORTRAIT),
                image_alt="Leopold Buczkowski, portret.",
                status=PUBLISHED,
            )
        )
        saved(MaterialWorkLink(material=portrait, work=works["wertepy"]))
        saved(
            Note(
                title="Notes 19 (szkic)",
                content_kind=ContentKind.EXTERNAL_MEDIA,
                external_url="https://example.com/notes-19",
            )
        )  # a draft

        self.spread_tags(tags)
        # Index again with the works and tags added after saving, as the editor panel does.
        for item in (note, letter, review, portrait):
            item.update_search_entry()
        Tag.update_search_entries()
        self.load_site_content()

    def load_work(
        self,
        data: WorkData,
        institution: Institution,
        tags: dict[str, Tag],
    ) -> Work:
        work = saved(
            Work(
                slug=data.slug,
                title=data.title,
                genre="powieść",
                description=data.description,
                cover_image=image(COVER),
                cover_image_alt=f"Okładka utworu „{data.title}” (zastępcza).",
                status=PUBLISHED,
            )
        )
        for publisher, place, year in data.editions:
            saved(Edition(work=work, publisher=publisher, place=place, year=year))
        for typescript_data in data.typescripts:
            document = ocr_document(typescript_data.scan)
            saved(
                Typescript(
                    work=work,
                    title=typescript_data.title,
                    institution=institution,
                    shelfmark=typescript_data.shelfmark,
                    is_main=typescript_data.is_main,
                    document=document,
                    status=PUBLISHED,
                )
            )
            sentences = spread_sentences(document.text, typescript_data.fragments)
            for number, sentence in enumerate(sentences, start=1):
                shown = {
                    "shelfmark": f"{typescript_data.shelfmark}.{number * 5 + 4:04d}",
                    **SHOWN_FRAGMENTS.get((typescript_data.shelfmark, number), {}),
                }
                fragment_tags = shown.pop("tags", [])
                fragment = saved(
                    Fragment(document=document, start=sentence.start(), end=sentence.end(), **shown)
                )
                fragment.tags.add(*(tags[name] for name in fragment_tags))
        return work

    def spread_tags(self, tags: dict[str, Tag]) -> None:
        """Tag the fragments the design does not show, in turn, until every tag has the design's
        number of occurrences."""
        occurrences = {tag.pk: tag.occurrences for tag in Tag.objects.with_occurrences()}
        fragments = list(Fragment.objects.visible().filter(tags__isnull=True).order_by("pk"))
        planned: dict[Fragment, list[Tag]] = {fragment: [] for fragment in fragments}
        position = 0
        for name, total in TAGS.items():
            for _ in range(total - occurrences[tags[name].pk]):
                planned[fragments[position % len(fragments)]].append(tags[name])
                position += 1
        for fragment, fragment_tags in planned.items():
            fragment.tags.add(*fragment_tags)

    def load_site_content(self) -> None:
        site = SiteSettings.load()
        site.intro_text = (
            "Archiwum literackie Leopolda Buczkowskiego: utwory, maszynopisy, zapiski i fragmenty "
            "połączone tagami."
        )
        site.portrait = image(PORTRAIT)
        site.portrait_alt = "Leopold Buczkowski, portret."
        site.about_intro = site.intro_text
        site.about_project = (
            "[Opis projektu: cel archiwum, zakres zbiorów, instytucje partnerskie i źródło "
            "finansowania. Dwa, trzy akapity.]"
        )
        saved(site)
        for order, group in enumerate(TeamMember.Group):
            saved(
                TeamMember(
                    name="[Imię i nazwisko]",
                    role="[Rola w projekcie]",
                    bio="[Biogram: dwa, trzy zdania]",
                    group=group,
                    order=order,
                )
            )
