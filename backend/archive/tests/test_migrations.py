import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = ("archive", "0007_remove_fragment_description")
AFTER = ("archive", "0008_fragment_unit_and_scan_number")


@pytest.mark.django_db(transaction=True)
class TestFragmentShelfmarkSplit:
    def test_arc_7_existing_shelfmarks_are_split_at_the_dot(self) -> None:
        # Arrange
        executor = MigrationExecutor(connection)
        executor.migrate([BEFORE])
        apps = executor.loader.project_state([BEFORE]).apps
        document = apps.get_model("archive", "Document").objects.create(kind="plain", text="x" * 30)
        Fragment = apps.get_model("archive", "Fragment")
        for start, shelfmark in ((0, "1618.0009"), (10, "1618"), (20, "")):
            Fragment.objects.create(
                document=document,
                start=start,
                end=start + 5,
                quote="xxxxx",
                shelfmark=shelfmark,
                location="rozdział I",
            )

        # Act
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

        # Assert
        Fragment = executor.loader.project_state([AFTER]).apps.get_model("archive", "Fragment")
        split = Fragment.objects.order_by("start").values_list("unit_number", "scan_number")
        assert list(split) == [("1618", "0009"), ("1618", ""), ("", "")]
