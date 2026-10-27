from pathlib import Path

from django.http import StreamingHttpResponse
from django.test import Client
from pytest_django.fixtures import Settings


def test_serve_local_media_reads_media_root_at_request_time(
    client: Client, settings: Settings, tmp_path: Path
) -> None:
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "note.txt").write_text("scan", encoding="utf-8")

    response = client.get("/media/note.txt")

    assert response.status_code == 200
    assert isinstance(response, StreamingHttpResponse)
    assert response.getvalue() == b"scan"
