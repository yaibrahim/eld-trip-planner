"""Vercel Python serverless entrypoint.

Vercel's @vercel/python builder loads this file and calls the WSGI
callable named `app`. On cold start we run migrations against a SQLite
file in /tmp (the only writable path in the serverless filesystem) since
there is no separate build step to run `manage.py migrate` first.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

try:
    call_command("migrate", "--noinput")
except Exception:
    pass

from config.wsgi import application as app  # noqa: E402
