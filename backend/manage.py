#!/usr/bin/env python
import os
import sys
from pathlib import Path

from config.dotenv import load_dotenv


def main() -> None:
    # Make exports `.env`; bare `uv run python backend/manage.py …` does not.
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
