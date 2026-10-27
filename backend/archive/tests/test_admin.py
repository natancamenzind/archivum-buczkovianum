from typing import Any

import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Model
from django.forms import ModelForm
from django.test import Client, RequestFactory
from django.urls import reverse
from django_prose_editor.fields import ProseEditorFormField
from pytest_django import DjangoAssertNumQueries

from archive.models import Document, Fragment, SiteSettings, Status, Tag
from archive.tests.factories import (
    DocumentFactory,
    FragmentFactory,
    MaterialWorkLinkFactory,
    NoteFactory,
    SecondaryTextFactory,
    SecondaryTextWorkLinkFactory,
    SiteSettingsFactory,
    TagFactory,
    TypescriptFactory,
    WorkFactory,
)

MODELS = [model for model in admin.site._registry if model._meta.app_label == "archive"]


@pytest.mark.django_db
class TestEditorPanel:
    @pytest.mark.parametrize("model", MODELS, ids=lambda model: model.__name__)
    def test_every_list_page_opens(self, admin_client: Client, model: type[Model]) -> None:
        # Arrange
        TypescriptFactory.create()
        FragmentFactory.create()
        SecondaryTextWorkLinkFactory.create()
        MaterialWorkLinkFactory.create()
        url = reverse(f"admin:archive_{model._meta.model_name}_changelist")

        # Act
        response = admin_client.get(url)

        # Assert
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "model", [m for m in MODELS if m is not Fragment], ids=lambda model: model.__name__
    )
    def test_every_add_page_opens(self, admin_client: Client, model: type[Model]) -> None:
        # Arrange
        url = reverse(f"admin:archive_{model._meta.model_name}_add")

        # Act
        response = admin_client.get(url)

        # Assert
        assert response.status_code == 200

    def test_us_wr_13_ac1_draft_has_a_view_on_site_link(self, admin_client: Client) -> None:
        # Arrange
        work = WorkFactory.create(slug="wertepy")
        url = reverse("admin:archive_work_change", args=[work.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        assert work.status == Status.DRAFT
        assert "viewsitelink" in response.content.decode()

    @pytest.mark.parametrize(("ocr", "text_editable"), [(True, False), (False, True)])
    def test_ocr_text_is_changed_only_by_uploading_a_new_ocr_file(
        self, admin_client: Client, ocr: bool, text_editable: bool
    ) -> None:
        # Arrange
        document = DocumentFactory.create(ocr=ocr)
        url = reverse("admin:archive_document_change", args=[document.pk])

        # Act
        response = admin_client.get(url)

        # Assert
        assert ('name="text"' in response.content.decode()) == text_editable

    @pytest.mark.parametrize("model", [Document, Fragment], ids=lambda model: model.__name__)
    def test_performance_changelist(
        self,
        admin_client: Client,
        django_assert_max_num_queries: DjangoAssertNumQueries,
        model: type[Model],
    ) -> None:
        # Arrange
        for factory in (TypescriptFactory, NoteFactory, SecondaryTextFactory):
            FragmentFactory.create_batch(
                3, document=factory.create(document=DocumentFactory.create()).document
            )
        url = reverse(f"admin:archive_{model._meta.model_name}_changelist")

        # Act & Assert
        with django_assert_max_num_queries(10):
            response = admin_client.get(url)
        assert response.status_code == 200

    def test_bulk_delete_action_is_disabled(self, admin_client: Client) -> None:
        # Arrange
        url = reverse("admin:archive_tag_changelist")

        # Act
        response = admin_client.get(url)

        # Assert
        assert "delete_selected" not in response.content.decode()

    def test_us_wr_08_ac3_deleting_a_tag_in_use_lists_its_usages(
        self, admin_client: Client
    ) -> None:
        # Arrange
        tag = TagFactory.create()
        FragmentFactory.create(document__text="Czarny potok płynie.").tags.add(tag)
        url = reverse("admin:archive_tag_delete", args=[tag.pk])

        # Act
        response = admin_client.post(url, {"post": "yes"})

        # Assert
        assert "Czarny potok" in response.content.decode()
        assert Tag.objects.filter(pk=tag.pk).exists()

    def test_us_wr_09_ac2_fragments_are_not_added_by_hand(self, admin_client: Client) -> None:
        # Arrange
        url = reverse("admin:archive_fragment_add")

        # Act
        response = admin_client.get(url)

        # Assert
        assert response.status_code == 403

    def test_us_wr_11_site_settings_cannot_be_added_twice_or_deleted(
        self, rf: RequestFactory, admin_user: User
    ) -> None:
        # Arrange
        settings = SiteSettingsFactory.create()
        model_admin = admin.site.get_model_admin(SiteSettings)
        request = rf.get("/")
        request.user = admin_user

        # Act
        permissions = (
            model_admin.has_add_permission(request),
            model_admin.has_delete_permission(request, settings),
        )

        # Assert
        assert permissions == (False, False)

    def test_us_wr_11_ac1_settings_form_has_no_funding_note(
        self, rf: RequestFactory, admin_user: User
    ) -> None:
        # Arrange: the footer's funding note is hardcoded in the frontend (plan D7).
        model_admin = admin.site.get_model_admin(SiteSettings)
        request = rf.get("/")
        request.user = admin_user

        # Act
        fields = model_admin.get_fields(request)

        # Assert
        assert list(fields) == [
            "intro_text",
            "portrait",
            "portrait_alt",
            "about_intro",
            "about_project",
        ]


@pytest.mark.django_db
class TestRichTextInThePanel:
    @pytest.mark.parametrize(
        "model", ["work", "tag", "typescript", "note", "secondarytext", "contextualmaterial"]
    )
    def test_us_wr_03_ac1_descriptions_use_the_rich_text_editor(
        self, admin_client: Client, model: str
    ) -> None:
        # Act
        response = admin_client.get(reverse(f"admin:archive_{model}_add"))

        # Assert
        assert is_rich_text(response.context["adminform"].form, "description")

    def test_us_wr_12_ac1_about_and_home_texts_use_the_rich_text_editor(
        self, admin_client: Client
    ) -> None:
        # Arrange
        SiteSettingsFactory.create()

        # Act
        response = admin_client.get(reverse("admin:archive_sitesettings_change", args=[1]))

        # Assert
        form = response.context["adminform"].form
        assert [name for name in form.fields if is_rich_text(form, name)] == [
            "intro_text",
            "about_intro",
            "about_project",
        ]

    def test_us_wr_12_ac1_saving_the_about_page_sanitizes_its_texts(
        self, admin_client: Client
    ) -> None:
        # Arrange
        SiteSettingsFactory.create()
        url = reverse("admin:archive_sitesettings_change", args=[1])
        data = {
            "intro_text": "<p>Wstęp</p>",
            "portrait_alt": "",
            "about_intro": '<p onclick="steal()">O archiwum</p>',
            "about_project": "<p><strong>Cel</strong></p><script>steal()</script>",
        }

        # Act
        response = admin_client.post(url, data)

        # Assert
        assert response.status_code == 302
        settings = SiteSettings.load()
        assert (settings.about_intro, settings.about_project) == (
            "<p>O archiwum</p>",
            "<p><strong>Cel</strong></p>",
        )


def is_rich_text(form: ModelForm[Any], name: str) -> bool:
    return isinstance(form.fields[name], ProseEditorFormField)
