"""The search index (docs/architecture.md, section 6).

One `SearchEntry` row per published entity and per visible fragment. Archive models write and
remove their own rows from `save()` and `delete()`; this module knows nothing about them.
"""

import operator
from collections.abc import Sequence
from dataclasses import dataclass
from functools import reduce
from typing import Any

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import Value
from django.utils.translation import gettext_lazy as _


class EntityType(models.TextChoices):
    """Kinds of indexed entities, in the order of the groups of results (US-RA-15 AC3)."""

    WORK = "work", _("Work")
    TAG = "tag", _("Tag")
    FRAGMENT = "fragment", _("Fragment")
    NOTE = "note", _("Note")
    TYPESCRIPT = "typescript", _("Typescript")
    SECONDARY_TEXT = "secondary_text", _("Secondary text")
    MATERIAL = "material", _("Contextual material")


class Weight(models.TextChoices):
    """Relevance weights of indexed texts (architecture section 6)."""

    TITLE = "A"  # titles, tag names
    QUOTE = "B"  # tag descriptions, fragment quotes
    DESCRIPTION = "C"  # other descriptions
    TEXT = "D"  # document texts


@dataclass(frozen=True)
class IndexedContent:
    """What an entity puts in its search entry."""

    title: str
    url: str
    texts: Sequence[tuple[str, Weight]]
    work_ids: Sequence[int] = ()
    decades: Sequence[int] = ()
    has_scan: bool = False
    has_text: bool = False

    @property
    def body(self) -> str:
        """Plain text that snippets are cut from: every indexed text but the title."""
        return "\n\n".join(text for text, weight in self.texts if text and weight != Weight.TITLE)


class SearchEntry(models.Model):
    entity_type = models.CharField(max_length=20, choices=EntityType.choices)
    entity_id = models.PositiveBigIntegerField()
    title = models.CharField(max_length=255)
    url = models.CharField(max_length=500)
    body = models.TextField(blank=True)
    vector = SearchVectorField()
    work_ids = ArrayField(models.PositiveBigIntegerField(), default=list)
    decades = ArrayField(models.PositiveSmallIntegerField(), default=list)
    has_scan = models.BooleanField(default=False)
    has_text = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "search entries"
        constraints = (
            models.UniqueConstraint(
                fields=["entity_type", "entity_id"], name="one_entry_per_entity"
            ),
        )
        indexes = (
            GinIndex(fields=["vector"], name="search_entry_vector"),
            GinIndex(fields=["title"], opclasses=["gin_trgm_ops"], name="search_entry_title_trgm"),
            GinIndex(fields=["work_ids"], name="search_entry_work_ids"),
            GinIndex(fields=["decades"], name="search_entry_decades"),
        )

    def __str__(self) -> str:
        return f"{self.entity_type}: {self.title}"

    @classmethod
    def write(cls, entity_type: EntityType, entity_id: int, content: IndexedContent) -> None:
        """Create or replace the entry of one entity."""
        vector = reduce(
            operator.add,
            (
                SearchVector(Value(text), weight=weight, config=settings.SEARCH_TS_CONFIG)
                for text, weight in content.texts
            ),
        )
        cls.objects.update_or_create(
            entity_type=entity_type,
            entity_id=entity_id,
            defaults={
                "title": content.title[:255],
                "url": content.url,
                "body": content.body,
                "vector": vector,
                "work_ids": list(content.work_ids),
                "decades": list(content.decades),
                "has_scan": content.has_scan,
                "has_text": content.has_text,
            },
        )

    @classmethod
    def remove(cls, entity_type: EntityType, *entity_ids: int) -> None:
        cls.objects.filter(entity_type=entity_type, entity_id__in=entity_ids).delete()

    @classmethod
    def remove_fragments(cls, fragments: "models.QuerySet[Any]") -> None:
        """Remove the entries of a queryset of fragments, in one query."""
        cls.objects.filter(
            entity_type=EntityType.FRAGMENT, entity_id__in=fragments.values("pk")
        ).delete()
