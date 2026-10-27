from django.urls import path

from api.views import about, works

# The public, read-only API of the site's pages (docs/architecture.md, section 7).
urlpatterns = [
    path("about/", about, name="about"),
    path("works/", works, name="works"),
]
