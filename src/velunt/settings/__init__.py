"""Django settings for Velunt, split by environment.

`base` holds everything the environments share. Point `DJANGO_SETTINGS_MODULE`
at `velunt.settings.dev` or `velunt.settings.prod`, which both build on it.
"""

import os

from django.core.exceptions import ImproperlyConfigured


def get_bool_env(name, default=False):
    value = os.environ.get(name)
    if not value:
        return default
    return value.lower() in ("true", "1", "yes")


def get_str_env(name, default="", required=False):
    value = os.environ.get(name)
    if value:
        return value
    if required:
        raise ImproperlyConfigured(f"The environment variable {name} must be set")
    return default
