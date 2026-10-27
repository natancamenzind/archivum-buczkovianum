from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ArchiveConfig(AppConfig):
    name = "archive"
    verbose_name = _("Archive")
