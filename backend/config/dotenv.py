"""Load a repo-root `.env` into os.environ without overriding existing values."""

import os
from pathlib import Path


def load_dotenv(path: Path) -> None:
    """Set KEY=VALUE pairs from ``path`` when the key is not already in the environment.

    Missing files are ignored so CI (env vars only, no ``.env``) keeps working.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value
