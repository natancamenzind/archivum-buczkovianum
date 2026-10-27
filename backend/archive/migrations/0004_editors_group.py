from django.apps import apps as django_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations

EDITORS_GROUP_NAME = "Redaktorzy"


def create_editors_group(apps: migrations.state.StateApps, schema_editor: object) -> None:
    from django.contrib.auth.models import Group, Permission

    create_permissions(django_apps.get_app_config("archive"), verbosity=0)
    group, _ = Group.objects.get_or_create(name=EDITORS_GROUP_NAME)
    permissions = Permission.objects.filter(content_type__app_label="archive")
    group.permissions.set(permissions)


def remove_editors_group(apps: migrations.state.StateApps, schema_editor: object) -> None:
    from django.contrib.auth.models import Group

    Group.objects.filter(name=EDITORS_GROUP_NAME).delete()


class Migration(migrations.Migration):
    dependencies = (
        ("archive", "0003_remove_sitesettings_funding_note"),
        ("auth", "0012_alter_user_first_name_max_length"),
    )

    operations = (migrations.RunPython(create_editors_group, remove_editors_group),)
