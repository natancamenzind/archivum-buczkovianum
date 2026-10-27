from django.urls import path

from api.editor_fragments import EditorFragmentDetail, EditorFragmentListCreate
from api.views import about, document, search_autocomplete, tags, typescript, typescripts, works

# The public, read-only API of the site's pages (docs/architecture.md, section 7).
urlpatterns = [
    path("about/", about, name="about"),
    path("works/", works, name="works"),
    path("typescripts/", typescripts, name="typescripts"),
    path("tags/", tags, name="tags"),
    path("search/autocomplete/", search_autocomplete, name="search-autocomplete"),
    path("typescripts/<int:pk>/", typescript, name="typescript"),
    path("documents/<int:pk>/", document, name="document"),
    path("editor/fragments/", EditorFragmentListCreate.as_view(), name="editor-fragments"),
    path("editor/fragments/<int:pk>/", EditorFragmentDetail.as_view(), name="editor-fragment"),
]
