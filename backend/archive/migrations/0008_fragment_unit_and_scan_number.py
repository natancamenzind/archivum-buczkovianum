from django.db import migrations, models


def split_shelfmarks(apps: migrations.state.StateApps, schema_editor: object) -> None:
    Fragment = apps.get_model("archive", "Fragment")
    for fragment in Fragment.objects.exclude(shelfmark=""):
        unit, _, scan = fragment.shelfmark.partition(".")
        Fragment.objects.filter(pk=fragment.pk).update(unit_number=unit, scan_number=scan)


def join_shelfmarks(apps: migrations.state.StateApps, schema_editor: object) -> None:
    Fragment = apps.get_model("archive", "Fragment")
    for fragment in Fragment.objects.exclude(unit_number="", scan_number=""):
        shelfmark = ".".join(part for part in (fragment.unit_number, fragment.scan_number) if part)
        Fragment.objects.filter(pk=fragment.pk).update(shelfmark=shelfmark)


class Migration(migrations.Migration):
    dependencies = (("archive", "0007_remove_fragment_description"),)

    operations = (
        migrations.AddField(
            model_name="fragment",
            name="unit_number",
            field=models.CharField(
                blank=True,
                help_text="The shelfmark before the dot, e.g. 1618; institution from the document.",
                max_length=50,
                verbose_name="archival unit number",
            ),
        ),
        migrations.AddField(
            model_name="fragment",
            name="scan_number",
            field=models.CharField(
                blank=True,
                help_text="The shelfmark after the dot, e.g. 0009: the scan in the archival unit.",
                max_length=50,
                verbose_name="scan number",
            ),
        ),
        migrations.RunPython(split_shelfmarks, join_shelfmarks),
        migrations.RemoveField(
            model_name="fragment",
            name="shelfmark",
        ),
        migrations.RemoveField(
            model_name="fragment",
            name="location",
        ),
    )
