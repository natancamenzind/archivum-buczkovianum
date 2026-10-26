from django.urls import re_path

from site_shell.views import index

# Included last in config/urls.py. Matches every path except those Django serves itself.
# `api` and `admin` without a trailing slash are excluded too, so APPEND_SLASH still redirects them.
urlpatterns = [
    re_path(r"^(?!(?:api|admin|static|media)(?:/|$)).*$", index, name="site_shell"),
]
