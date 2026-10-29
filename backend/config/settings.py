"""Django settings. All configuration comes from environment variables."""

import os
from pathlib import Path

import dj_database_url
import django_stubs_ext
from django.core.exceptions import ImproperlyConfigured

# Makes Django generics such as `ModelAdmin[Work]` subscriptable at runtime, for mypy.
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent


def env_list(name: str) -> list[str]:
    """Read a comma-separated environment variable, skipping empty items."""
    return [item for item in os.environ.get(name, "").split(",") if item]


DEBUG = os.environ.get("DEBUG", "false").lower() == "true"

# With DEBUG=True media falls back to the local filesystem, so only these are needed.
REQUIRED_ENV = ("SECRET_KEY", "DATABASE_URL")
PRODUCTION_REQUIRED_ENV = (
    *REQUIRED_ENV,
    "ALLOWED_HOSTS",
    "CSRF_TRUSTED_ORIGINS",
    "AWS_STORAGE_BUCKET_NAME",
    "AWS_S3_REGION_NAME",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
)
for name in REQUIRED_ENV if DEBUG else PRODUCTION_REQUIRED_ENV:
    if not os.environ.get(name):
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")

SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

if not DEBUG:
    # Railway's edge terminates HTTPS and tells Django the original scheme in X-Forwarded-Proto.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "django_prose_editor",
    "archive",
    "search",
    "api",
    "site_shell",
]

# The test environment's guards (US-OPS-01 AC3, AC4), off unless their variables are set.
BASIC_AUTH_USER = os.environ.get("BASIC_AUTH_USER", "")
BASIC_AUTH_PASSWORD = os.environ.get("BASIC_AUTH_PASSWORD", "")
ROBOTS_NOINDEX = os.environ.get("ROBOTS_NOINDEX", "false").lower() == "true"

MIDDLEWARE = [
    # First, so even a 401 from basic auth carries X-Robots-Tag.
    "config.middleware.NoindexMiddleware",
    "config.middleware.BasicAuthMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pl"
# Polish for the editor panel's own strings, written in English in the code (`make messages`).
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# The built frontend (`npm run build`): site_shell serves its index.html, and its assets are static
# files under STATIC_URL. Listed only once built, so a backend-only checkout gets no warning.
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"
STATICFILES_DIRS = [FRONTEND_DIST_DIR] if FRONTEND_DIST_DIR.is_dir() else []
# Files whose name carries a content hash are cached forever: Vite's build output
# (assets/index-B2gSypW-.js) and the copies collectstatic hashes (base.6b1c3d0e4f5a.css).
WHITENOISE_IMMUTABLE_FILE_TEST = r"/(assets/[^/]+-[\w-]{8}|[^/]+\.[0-9a-f]{12})\.\w+$"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Media goes to S3 when a bucket is configured, otherwise to the local filesystem.
# django-storages reads credentials from the environment itself, but these only from settings.
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME") or None
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL") or None
# The bucket is private: uploads get no public ACL and every media URL is presigned.
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage"
        if AWS_STORAGE_BUCKET_NAME
        else "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Sessions only, and it must stay that way. The test environment sits behind HTTP basic auth
    # (BasicAuthMiddleware, US-OPS-01 AC3), so every request carries an Authorization: Basic
    # header. DRF's BasicAuthentication would try those site credentials as a Django user and
    # reject every API request that is not also a Django login with the same password.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Archivum Buczkovianum API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# PostgreSQL 19 ships `polish`. A dev database without it may set `simple`, losing only
# inflection (docs/plan.md, D17).
SEARCH_TS_CONFIG = os.environ.get("SEARCH_TS_CONFIG", "polish")

# How many items a section preview shows before its "all" link (R-09).
PREVIEW_LIMIT = 2
