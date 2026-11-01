"""Settings for production, configured through environment variables"""

from . import get_bool_env, get_str_env
from .base import *  # noqa: F403

DEBUG = get_bool_env("DJANGO_DEBUG", default=False)

SECRET_KEY = get_str_env("DJANGO_SECRET_KEY", required=True)

ALLOWED_HOSTS = get_str_env("DJANGO_ALLOWED_HOSTS", required=True).split(",")

DATABASES["default"]["PASSWORD"] = get_str_env("POSTGRES_PASSWORD", required=True)  # noqa: F405
