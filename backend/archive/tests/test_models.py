import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from pytest_django import DjangoAssertNumQueries

from archive.models import (
    ContentKind,
    Document,
    Institution,
    SiteSettings,
    Status,
    Taggable,
    TeamMember,
    Work,
)
from archive.tests.factories import (
    ContextualMaterialFactory,
    DocumentFactory,
    EditionFactory,
    FragmentFactory,
    InstitutionFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    SiteSettingsFactory,
    TagFactory,
    TeamMemberFactory,
    TypescriptFactory,
    WorkFactory,
)


@pytest.mark.django_db
class TestAltText:
    def test_r_12_image_without_alt_is_rejected(self) -> None:
        # Arrange
        work = WorkFactory.create(
            cover_image=ContentFile(b"img", name="cover.png"), cover_image_alt=""
        )

        # Act
        with pytest.raises(ValidationError) as error:
            work.full_clean()

        # Assert
        assert "cover_image_alt" in error.value.message_dict

    def test_r_12_image_with_alt_is_accepted(self) -> None:
        # Arrange
        work = WorkFactory.create(
            cover_image=ContentFile(b"img", name="cover.png"), cover_image_alt="Okładka"
        )

        # Act
        work.full_clean()

        # Assert
        assert work.cover_image_alt == "Okładka"


@pytest.mark.django_db
class TestPublishable:
    def test_us_wr_02_ac1_new_entity_is_a_draft(self) -> None:
        # Arrange
        work = WorkFactory.create()

        # Act
        status = work.status

        # Assert
        assert status == Status.DRAFT

    def test_us_wr_13_ac1_every_entity_has_a_site_url(self) -> None:
        # Arrange
        work = WorkFactory.create(slug="wertepy")
        tag = TagFactory.create(slug="potok")
        typescript = TypescriptFactory.create()
        note = NoteFactory.create()
        text = SecondaryTextFactory.create()
        material = ContextualMaterialFactory.create()

        # Act
        urls = [
            entity.get_absolute_url() for entity in (work, tag, typescript, note, text, material)
        ]

        # Assert
        assert urls == [
            "/works/wertepy",
            "/tags/potok",
            f"/typescripts/{typescript.pk}",
            f"/notes/{note.pk}",
            f"/secondary-texts/{text.pk}",
            f"/materials/{material.pk}",
        ]


@pytest.mark.django_db
class TestShelfmark:
    @pytest.mark.parametrize(
        ("abbreviation", "number", "expected"),
        [("ML", "1618", "ML, sygn. 1618"), (None, "1618", "sygn. 1618"), ("ML", "", "")],
    )
    def test_us_wr_14_ac2_shelfmark_is_built_from_institution_and_number(
        self, abbreviation: str | None, number: str, expected: str
    ) -> None:
        # Arrange
        institution = InstitutionFactory.create(abbreviation=abbreviation) if abbreviation else None
        typescript = TypescriptFactory.create(institution=institution, shelfmark=number)

        # Act
        display = typescript.shelfmark_display

        # Assert
        assert display == expected

    def test_us_wr_09_ac6_fragment_takes_institution_from_its_document(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create(
            institution=InstitutionFactory.create(abbreviation="ML")
        )
        fragment = FragmentFactory.create(document=typescript.document, shelfmark="1618.0009")

        # Act
        display = fragment.shelfmark_display

        # Assert
        assert display == "ML, sygn. 1618.0009"

    def test_us_wr_14_ac1_institution_in_use_cannot_be_deleted(self) -> None:
        # Arrange
        institution = InstitutionFactory.create()
        TypescriptFactory.create(institution=institution)

        # Act
        with pytest.raises(ProtectedError):
            institution.delete()

        # Assert
        assert Institution.objects.filter(pk=institution.pk).exists()


@pytest.mark.django_db
class TestArchival:
    def test_us_wr_04_ac1_typescript_without_text_is_rejected(self) -> None:
        # Arrange
        typescript = TypescriptFactory.build(work=WorkFactory.create(), document=None)

        # Act
        with pytest.raises(ValidationError) as error:
            typescript.full_clean()

        # Assert
        assert "document" in error.value.message_dict

    def test_us_wr_04_ac1_typescript_with_plain_text_is_rejected(self) -> None:
        # Arrange
        typescript = TypescriptFactory.build(
            work=WorkFactory.create(), document=DocumentFactory.create()
        )

        # Act
        with pytest.raises(ValidationError) as error:
            typescript.full_clean()

        # Assert
        assert "document" in error.value.message_dict

    @pytest.mark.parametrize("ocr", [True, False])
    def test_us_wr_06_ac1_secondary_text_takes_ocr_or_plain_text(self, ocr: bool) -> None:
        # Arrange
        text = SecondaryTextFactory.create(document=DocumentFactory.create(ocr=ocr))

        # Act
        text.clean()

        # Assert
        assert text.document is not None

    def test_deleting_an_item_deletes_its_document(self) -> None:
        # Arrange
        secondary_text = SecondaryTextFactory.create()
        document_pk = secondary_text.document_id
        assert document_pk is not None

        # Act
        secondary_text.delete()

        # Assert
        assert not Document.objects.filter(pk=document_pk).exists()

    def test_deleting_an_item_without_document_works(self) -> None:
        # Arrange
        note = NoteFactory.create()

        # Act
        note.delete()

        # Assert
        assert note.pk is None

    def test_us_wr_05_saving_an_item_without_its_text_deletes_the_text(self) -> None:
        # Arrange
        secondary_text = SecondaryTextFactory.create()
        dropped = secondary_text.document
        assert dropped is not None
        secondary_text.refresh_from_db()
        secondary_text.document = DocumentFactory.create()

        # Act
        secondary_text.full_clean()
        secondary_text.save()

        # Assert
        assert not Document.objects.filter(pk=dropped.pk).exists()

    def test_us_wr_09_ac4_a_text_with_fragments_is_never_dropped(self) -> None:
        # Arrange
        secondary_text = SecondaryTextFactory.create()
        assert secondary_text.document is not None
        FragmentFactory.create_batch(2, document=secondary_text.document)
        secondary_text.refresh_from_db()
        secondary_text.document = DocumentFactory.create()

        # Act
        with pytest.raises(ValidationError) as error:
            secondary_text.full_clean()

        # Assert
        assert error.value.message_dict == {
            "document": [
                "The text this item holds has 2 tagged fragments. "
                "Delete them before removing the text."
            ]
        }

    def test_a_text_belongs_to_one_item_only(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create()
        note = NoteFactory.build(content_kind=ContentKind.OCR_TEXT, document=typescript.document)

        # Act
        with pytest.raises(ValidationError) as error:
            note.clean()

        # Assert
        assert "document" in error.value.message_dict


@pytest.mark.django_db
class TestMediaContent:
    @pytest.mark.parametrize(
        ("content_kind", "missing_field"),
        [
            (ContentKind.IMAGE, "image"),
            (ContentKind.DOCUMENT, "file"),
            (ContentKind.EXTERNAL_MEDIA, "external_url"),
        ],
    )
    def test_us_wr_05_ac2_content_kind_requires_its_field(
        self, content_kind: ContentKind, missing_field: str
    ) -> None:
        # Arrange
        note = NoteFactory.create(content_kind=content_kind, external_url="")

        # Act
        with pytest.raises(ValidationError) as error:
            note.full_clean()

        # Assert
        assert missing_field in error.value.message_dict

    @pytest.mark.parametrize(
        ("content_kind", "document_kind"),
        [(ContentKind.OCR_TEXT, Document.Kind.PLAIN), (ContentKind.PLAIN_TEXT, None)],
    )
    def test_us_wr_07_ac2_text_content_requires_matching_document(
        self, content_kind: ContentKind, document_kind: Document.Kind | None
    ) -> None:
        # Arrange
        document = DocumentFactory.create(kind=document_kind) if document_kind else None
        material = ContextualMaterialFactory.create(
            content_kind=content_kind, document=document, external_url=""
        )

        # Act
        with pytest.raises(ValidationError) as error:
            material.full_clean()

        # Assert
        assert "document" in error.value.message_dict

    def test_us_wr_05_ac2_missing_content_kind_is_a_form_error(self) -> None:
        # Arrange
        note = NoteFactory.build(content_kind="")

        # Act
        with pytest.raises(ValidationError) as error:
            note.full_clean()

        # Assert
        assert "content_kind" in error.value.message_dict

    def test_us_wr_05_ac2_plain_text_note_is_valid(self) -> None:
        # Arrange
        note = NoteFactory.create(
            content_kind=ContentKind.PLAIN_TEXT, document=DocumentFactory.create(), external_url=""
        )
        note.works.add(WorkFactory.create())

        # Act
        note.full_clean()

        # Assert
        assert note.document is not None

    @pytest.mark.parametrize(
        ("leftover", "value"),
        [("document", "document"), ("file", ContentFile(b"%PDF", name="old.pdf"))],
    )
    def test_us_wr_05_ac2_fields_of_another_content_kind_are_rejected(
        self, leftover: str, value: object
    ) -> None:
        # Arrange
        note = NoteFactory.create(content_kind=ContentKind.EXTERNAL_MEDIA)
        setattr(note, leftover, DocumentFactory.create() if value == "document" else value)

        # Act
        with pytest.raises(ValidationError) as error:
            note.clean()

        # Assert
        assert leftover in error.value.message_dict


@pytest.mark.django_db
class TestTag:
    def test_us_wr_08_ac2_related_tags_are_symmetric(self) -> None:
        # Arrange
        a, b = TagFactory.create(), TagFactory.create()

        # Act
        b.related.add(a)

        # Assert
        assert list(a.related.all()) == [b]

    def test_us_wr_08_ac3_tag_in_use_cannot_be_deleted(self) -> None:
        # Arrange
        tag = TagFactory.create()
        FragmentFactory.create().tags.add(tag)
        MaterialWorkLinkFactory.create().tags.add(tag)

        # Act
        with pytest.raises(ProtectedError) as error:
            tag.delete()

        # Assert
        assert len(error.value.protected_objects) == 2

    def test_us_wr_08_ac3_unused_tag_can_be_deleted(self) -> None:
        # Arrange
        tag = TagFactory.create()

        # Act
        tag.delete()

        # Assert
        assert tag.pk is None

    def test_us_wr_08_ac3_usages_are_limited(self) -> None:
        # Arrange
        tag = TagFactory.create()
        for work in WorkFactory.create_batch(3):
            work.tags.add(tag)
        FragmentFactory.create().tags.add(tag)

        # Act
        usages = tag.usages(limit=2)

        # Assert
        assert len(usages) == 2

    def test_us_wr_10_usages_cover_entities_fragments_and_work_links(self) -> None:
        # Arrange
        tag = TagFactory.create()
        tagged: list[Taggable] = [
            WorkFactory.create(),
            FragmentFactory.create(),
            SecondaryTextWorkLinkFactory.create(),
        ]
        for item in tagged:
            item.tags.add(tag)

        # Act
        usages = tag.usages()

        # Assert
        assert set(usages) == set(tagged)


@pytest.mark.django_db
class TestWork:
    def test_us_ra_18_ac2_works_are_ordered_by_first_edition(self) -> None:
        # Arrange
        later, earlier, undated = WorkFactory.create(), WorkFactory.create(), WorkFactory.create()
        EditionFactory.create(work=later, year=1966)
        EditionFactory.create(work=later, year=1958)
        EditionFactory.create(work=earlier, year=1947)

        # Act
        works = list(Work.objects.with_year())

        # Assert
        assert works == [earlier, later, undated]

    def test_editions_institutions_and_work_links_have_readable_names(self) -> None:
        # Arrange
        work = WorkFactory.create(title="Wertepy")
        edition = EditionFactory.create(work=work, publisher="Czytelnik", place="Warszawa")
        text_link = SecondaryTextWorkLinkFactory.create(work=work, secondary_text__title="Recenzja")
        material_link = MaterialWorkLinkFactory.create(work=work, material__title="Zdjęcie")

        # Act
        names = [str(edition), str(InstitutionFactory.create()), str(text_link), str(material_link)]

        # Assert
        assert names == [
            "Czytelnik, Warszawa 1947",
            "ML",
            "Recenzja ↔ Wertepy",
            "Zdjęcie ↔ Wertepy",
        ]


@pytest.mark.django_db
class TestTypescript:
    def test_us_wr_04_ac3_marking_main_unmarks_previous(self) -> None:
        # Arrange
        previous = TypescriptFactory.create(is_main=True)
        other_work_main = TypescriptFactory.create(is_main=True)

        # Act
        TypescriptFactory.create(work=previous.work, is_main=True)

        # Assert
        previous.refresh_from_db()
        other_work_main.refresh_from_db()
        assert not previous.is_main
        assert other_work_main.is_main

    def test_us_wr_04_ac3_database_allows_one_main_typescript_per_work(self) -> None:
        # Arrange
        main = TypescriptFactory.create(is_main=True)
        second = TypescriptFactory.create(work=main.work)

        # Act
        with pytest.raises(IntegrityError):
            type(second).objects.filter(pk=second.pk).update(is_main=True)

        # Assert
        assert main.is_main

    def test_us_wr_04_ac3_marking_main_passes_form_validation(self) -> None:
        # Arrange
        previous = TypescriptFactory.create(is_main=True)
        typescript = TypescriptFactory.create(work=previous.work)
        typescript.is_main = True

        # Act
        typescript.full_clean()

        # Assert
        assert typescript.is_main


@pytest.mark.django_db
class TestDocument:
    def test_set_ocr_text_splits_pages_on_form_feed(self) -> None:
        # Arrange
        document = DocumentFactory.build(kind=Document.Kind.OCR)

        # Act
        document.set_ocr_text("one\ntwo\n\fthree\n\f")

        # Assert
        assert document.text == "one\ntwo\nthree\n"
        assert document.page_offsets == [0, 8]
        assert document.page_count == 2

    @pytest.mark.parametrize(("offset", "page"), [(0, 1), (7, 1), (8, 2), (13, 2)])
    def test_page_number_of_an_offset(self, offset: int, page: int) -> None:
        # Arrange
        document = DocumentFactory.build(page_offsets=[0, 8])

        # Act
        number = document.page_number(offset)

        # Assert
        assert number == page

    def test_plain_text_has_no_page_number(self) -> None:
        # Arrange
        document = DocumentFactory.build()

        # Act
        number = document.page_number(3)

        # Assert
        assert number is None

    def test_us_wr_04_ac1_ocr_text_without_scan_is_rejected(self) -> None:
        # Arrange
        document = DocumentFactory.build(kind=Document.Kind.OCR)

        # Act
        with pytest.raises(ValidationError) as error:
            document.full_clean()

        # Assert
        assert "scan" in error.value.message_dict

    def test_plain_text_with_scan_is_rejected(self) -> None:
        # Arrange
        document = DocumentFactory.build(scan=ContentFile(b"%PDF", name="scan.pdf"))

        # Act
        with pytest.raises(ValidationError) as error:
            document.full_clean()

        # Assert
        assert "scan" in error.value.message_dict

    def test_owner_and_name_come_from_the_item_holding_the_text(self) -> None:
        # Arrange
        typescript = TypescriptFactory.create(title="Pierwsza wersja")
        assert typescript.document is not None

        # Act
        owner = typescript.document.owner

        # Assert
        assert owner == typescript
        assert str(typescript.document) == "Pierwsza wersja"

    def test_document_without_owner(self) -> None:
        # Arrange
        document = DocumentFactory.create()

        # Act
        owner = document.owner

        # Assert
        assert owner is None
        assert str(document) == f"Plain text #{document.pk}"

    def test_saving_without_text_change_skips_fragments(
        self, django_assert_max_num_queries: DjangoAssertNumQueries
    ) -> None:
        # Arrange
        document = DocumentFactory.create()
        FragmentFactory.create_batch(3, document=document)

        # Act
        with django_assert_max_num_queries(3) as queries:
            document.save()

        # Assert
        assert not any("archive_fragment" in query["sql"] for query in queries.captured_queries)

    def test_ocr_text_changes_only_with_its_page_boundaries(self) -> None:
        # Arrange
        document = Document.objects.get(pk=DocumentFactory.create(ocr=True).pk)
        document.text = "Poprawiony tekst."

        # Act
        with pytest.raises(ValidationError) as error:
            document.clean()

        # Assert
        assert "text" in error.value.message_dict

    def test_new_ocr_file_may_change_the_text(self) -> None:
        # Arrange
        document = Document.objects.get(pk=DocumentFactory.create(ocr=True).pk)
        document.set_ocr_text("Strona 1\fStrona 2")

        # Act
        document.clean()

        # Assert
        assert document.page_offsets == [0, 8]


@pytest.mark.django_db
class TestFragment:
    def test_us_wr_09_ac4_quote_is_copied_from_the_text(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok płynie.")

        # Act
        fragment = FragmentFactory.create(document=document, start=7, end=12)

        # Assert
        assert fragment.quote == "potok"
        assert str(fragment) == "potok"

    def test_us_wr_09_ac4_unchanged_quote_keeps_fragment(self) -> None:
        # Arrange
        fragment = FragmentFactory.create(
            document=DocumentFactory.create(text="Czarny potok."), start=7, end=12
        )
        fragment.document.text = "Czarny potok płynie."

        # Act
        fragment.document.save()

        # Assert
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (7, 12, False)

    def test_us_wr_09_ac4_quote_found_once_is_moved_and_flagged(self) -> None:
        # Arrange
        fragment = FragmentFactory.create(
            document=DocumentFactory.create(text="Czarny potok."), start=7, end=12
        )
        fragment.document.text = "Nowy wstęp. Czarny potok."

        # Act
        fragment.document.save()

        # Assert
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (19, 24, True)

    @pytest.mark.parametrize("new_text", ["Biały strumień.", "potok i potok"])
    def test_us_wr_09_ac4_lost_or_ambiguous_quote_is_flagged_not_deleted(
        self, new_text: str
    ) -> None:
        # Arrange
        fragment = FragmentFactory.create(
            document=DocumentFactory.create(text="Czarny potok."), start=7, end=12
        )
        fragment.document.text = new_text

        # Act
        fragment.document.save()

        # Assert
        fragment.refresh_from_db()
        assert fragment.needs_review
        assert fragment.quote == "potok"

    def test_us_wr_09_ac3_fragments_may_overlap(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok płynie.")
        FragmentFactory.create(document=document, start=0, end=12)

        # Act
        FragmentFactory.create(document=document, start=7, end=19)

        # Assert
        assert document.fragments.count() == 2

    def test_fragment_past_the_end_of_text_is_rejected(self) -> None:
        # Arrange
        fragment = FragmentFactory.build(document=DocumentFactory.create(text="Krótki."), end=50)

        # Act
        with pytest.raises(ValidationError):
            fragment.clean()

        # Assert
        assert fragment.pk is None

    def test_empty_fragment_is_rejected_by_the_database(self) -> None:
        # Arrange
        document = DocumentFactory.create()

        # Act
        with pytest.raises(IntegrityError):
            FragmentFactory.create(document=document, start=5, end=5, quote="x")

        # Assert
        assert document.pk is not None

    def test_start_page_follows_page_offsets(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="aaaa bbbb", page_offsets=[0, 5])

        # Act
        fragment = FragmentFactory.create(document=document, start=5, end=9)

        # Assert
        assert fragment.start_page == 2

    def test_long_quote_is_shortened_in_its_name(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="x" * 100)

        # Act
        fragment = FragmentFactory.create(document=document, start=0, end=100)

        # Assert
        assert str(fragment) == "x" * 59 + "…"

    def test_us_wr_09_ac4_flagged_fragment_past_the_end_can_still_be_edited(self) -> None:
        # Arrange
        fragment = FragmentFactory.create(document=DocumentFactory.create(text="x" * 30))
        fragment.document.text = "short"
        fragment.document.save()
        fragment.refresh_from_db()
        fragment.description = "Sprawdzić."

        # Act
        fragment.full_clean()

        # Assert
        assert fragment.needs_review

    def test_us_wr_09_ac4_quote_restored_in_place_stays_flagged(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok.")
        fragment = FragmentFactory.create(document=document, start=7, end=12)
        document.text = "Biały strumień."
        document.save()
        document.text = "Czarny potok."

        # Act
        document.save()

        # Assert
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (7, 12, True)

    def test_us_wr_09_ac4_flagged_fragment_found_again_is_moved_and_stays_flagged(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok.")
        fragment = FragmentFactory.create(document=document, start=7, end=12)
        document.text = "Biały strumień."
        document.save()
        document.text = "Wstęp. Czarny potok."

        # Act
        document.save()

        # Assert
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (14, 19, True)

    def test_us_wr_09_ac4_flagged_fragment_still_lost_is_not_saved_again(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok.")
        fragment = FragmentFactory.create(document=document, start=7, end=12)
        document.text = "Biały strumień."
        document.save()
        fragment.refresh_from_db()
        flagged_at = fragment.updated_at
        document.text = "Biały strumień płynie."

        # Act
        document.save()

        # Assert
        fragment.refresh_from_db()
        assert fragment.updated_at == flagged_at

    def test_us_wr_09_ac4_reviewed_fragment_stays_unflagged_while_it_matches(self) -> None:
        # Arrange
        document = DocumentFactory.create(text="Czarny potok.")
        fragment = FragmentFactory.create(document=document, start=7, end=12)
        document.text = "Wstęp. Czarny potok."
        document.save()
        fragment.refresh_from_db()
        fragment.needs_review = False
        fragment.save()
        document.text = "Wstęp. Czarny potok płynie."

        # Act
        document.save()

        # Assert
        fragment.refresh_from_db()
        assert (fragment.start, fragment.end, fragment.needs_review) == (14, 19, False)


@pytest.mark.django_db
class TestSiteContent:
    def test_us_wr_11_ac1_site_settings_are_a_single_row(self) -> None:
        # Arrange
        SiteSettingsFactory.create()

        # Act
        with pytest.raises(IntegrityError), transaction.atomic():
            SiteSettingsFactory.create()

        # Assert
        assert str(SiteSettings.load()) == "Site settings"

    def test_us_wr_11_ac1_settings_are_created_on_first_load(self) -> None:
        # Arrange
        assert not SiteSettings.objects.exists()

        # Act
        settings = SiteSettings.load()

        # Assert
        assert settings.pk == 1

    def test_us_wr_12_ac2_team_members_are_ordered(self) -> None:
        # Arrange
        second = TeamMemberFactory.create(name="Anna", order=2)
        first = TeamMemberFactory.create(name="Zofia", order=1)

        # Act
        members = [str(member) for member in TeamMember.objects.all()]

        # Assert
        assert members == [str(first), str(second)]
