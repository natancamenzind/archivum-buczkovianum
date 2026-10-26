from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from archive.models import ContextualMaterial, Note, SecondaryText, Tag, Typescript, Work
from search.models import SearchEntry


class Command(BaseCommand):
    help = (
        "Rebuild the whole search index. Run it after bulk QuerySet operations, which skip "
        "save() and delete() (docs/architecture.md, section 6)."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        with transaction.atomic():
            SearchEntry.objects.all().delete()
            # Indexing an item also indexes the fragments of its document.
            for model in (Work, Tag, Typescript, Note, SecondaryText, ContextualMaterial):
                for entity in model.objects.published():
                    entity.update_search_entry()
        self.stdout.write(f"Indexed {SearchEntry.objects.count()} entries.")
