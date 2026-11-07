from django.urls import reverse

# The endpoint name (architecture section 7) of each entity page's first path segment (section 8).
ENDPOINTS = {
    "utwory": "work",
    "tagi": "tag",
    "maszynopisy": "typescript",
    "zapiski": "note",
    "teksty-sekundarne": "secondary-text",
    "materialy": "material",
}


def endpoint(page_path: str) -> str:
    """The endpoint that serves the entity page at `page_path`, e.g. `/utwory/wertepy`."""
    kind, key = page_path.strip("/").split("/")
    return reverse(ENDPOINTS[kind], args=[key])
