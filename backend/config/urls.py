from django.contrib import admin
from django.urls import include, path
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import SpectacularAPIView

# The schema documents its own endpoint while it is the only one, so the placeholder page can
# call it through the generated client (docs/plan.md, step 1).
# Drop this once the first page endpoint exists.
SchemaView = extend_schema_view(
    get=extend_schema(exclude=False, responses={200: OpenApiTypes.OBJECT}),
)(SpectacularAPIView)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SchemaView.as_view(), name="schema"),
    # Last: every other URL is a page of the public site.
    path("", include("site_shell.urls")),
]
