"""Settings for local development"""

from . import get_bool_env, get_str_env
from .base import *  # noqa: F403

DEBUG = get_bool_env("DJANGO_DEBUG", default=True)

SECRET_KEY = "insecure-dev-key"

ALLOWED_HOSTS = get_str_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
