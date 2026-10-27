from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/", include("api.urls")),
    # Last: every other URL is a page of the public site.
    path("", include("site_shell.urls")),
]
