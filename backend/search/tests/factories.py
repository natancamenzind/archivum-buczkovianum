from factory.declarations import Sequence
from factory.django import DjangoModelFactory

from search.models import EntityType, SearchEntry


class SearchEntryFactory(DjangoModelFactory[SearchEntry]):
    """A raw index row. Archive models write real entries themselves."""

    class Meta:
        model = SearchEntry

    entity_type = EntityType.WORK
    entity_id = Sequence(lambda n: n + 1000)
    title = Sequence(lambda n: f"Entry {n}")
    url = "/works/entry"
    vector = ""
