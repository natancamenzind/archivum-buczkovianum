from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView

from config.media_serving import serve_local_media

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/", include("api.urls")),
]

# Uploaded files live on S3 in production; locally they are served from MEDIA_ROOT.
if not settings.AWS_STORAGE_BUCKET_NAME:
    urlpatterns.append(re_path(r"^media/(?P<path>.*)$", serve_local_media))

# Last: every other URL is a page of the public site.
urlpatterns.append(path("", include("site_shell.urls")))
