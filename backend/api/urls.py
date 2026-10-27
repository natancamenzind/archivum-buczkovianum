from django.urls import path

from api.editor_fragments import EditorFragmentDetail, EditorFragmentListCreate
from api.views import about, works

# The public, read-only API of the site's pages (docs/architecture.md, section 7).
urlpatterns = [
    path("about/", about, name="about"),
    path("works/", works, name="works"),
    path("editor/fragments/", EditorFragmentListCreate.as_view(), name="editor-fragments"),
    path("editor/fragments/<int:pk>/", EditorFragmentDetail.as_view(), name="editor-fragment"),
]
