import pytest
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Model
from django.test import Client, RequestFactory
from django.urls import reverse
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
