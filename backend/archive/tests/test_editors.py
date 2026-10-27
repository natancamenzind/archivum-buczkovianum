import pytest
from django.contrib.auth.models import Group, Permission, User
from django.test import Client
from django.urls import NoReverseMatch, reverse

EDITORS_GROUP_NAME = "Redaktorzy"


@pytest.mark.django_db
class TestEditorsGroup:
    def test_us_wr_01_ac1_there_is_no_public_registration(self) -> None:
        # Arrange
        registration_route_names = ("register", "signup", "account_signup")

        # Act & Assert
        for name in registration_route_names:
            with pytest.raises(NoReverseMatch):
                reverse(name)

    def test_us_wr_01_ac2_redaktorzy_group_has_every_archive_permission(self) -> None:
        # Arrange
        archive_permissions = set(
            Permission.objects.filter(content_type__app_label="archive").values_list(
                "codename", flat=True
            )
        )

        # Act
        group = Group.objects.get(name=EDITORS_GROUP_NAME)
        group_permissions = set(group.permissions.values_list("codename", flat=True))

        # Assert
        assert group_permissions == archive_permissions

    def test_us_wr_01_ac2_editors_in_the_group_share_the_same_rights(self) -> None:
        # Arrange
        group = Group.objects.get(name=EDITORS_GROUP_NAME)
        first = User.objects.create_user(username="editor-a", password="secret", is_staff=True)
        second = User.objects.create_user(username="editor-b", password="secret", is_staff=True)
        first.groups.add(group)
        second.groups.add(group)

        # Act
        first_permissions = first.get_all_permissions()
        second_permissions = second.get_all_permissions()

        # Assert
        assert first_permissions == second_permissions
        assert first_permissions

    def test_editors_can_open_the_admin_work_list(self, client: Client) -> None:
        # Arrange
        group = Group.objects.get(name=EDITORS_GROUP_NAME)
        user = User.objects.create_user(username="editor", password="secret", is_staff=True)
        user.groups.add(group)
        client.force_login(user)
        url = reverse("admin:archive_work_changelist")

        # Act
        response = client.get(url)

        # Assert
        assert response.status_code == 200
