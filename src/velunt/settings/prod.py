"""Settings for production, configured through environment variables"""

from . import get_bool_env, get_str_env
from .base import *  # noqa: F403

DEBUG = get_bool_env("DJANGO_DEBUG", default=False)

SECRET_KEY = get_str_env("DJANGO_SECRET_KEY", required=True)

ALLOWED_HOSTS = get_str_env("DJANGO_ALLOWED_HOSTS", required=True).split(",")

DATABASES["default"]["PASSWORD"] = get_str_env("POSTGRES_PASSWORD", required=True)  # noqa: F405

# Production runs behind a TLS-terminating reverse proxy
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [f"https://{host}" for host in ALLOWED_HOSTS]
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_str_env("DJANGO_EMAIL_HOST", required=True)
EMAIL_PORT = int(get_str_env("DJANGO_EMAIL_PORT", "587"))
EMAIL_HOST_USER = get_str_env("DJANGO_EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = get_str_env("DJANGO_EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = get_bool_env("DJANGO_EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = get_str_env("DJANGO_DEFAULT_FROM_EMAIL", required=True)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Comma-separated addresses that receive server error reports
ADMINS = [
    ("", address.strip())
    for address in get_str_env("DJANGO_ADMINS").split(",")
    if address.strip()
]
