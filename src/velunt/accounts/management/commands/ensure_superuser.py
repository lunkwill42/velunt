import os
import secrets

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Create an initial superuser, unless one exists already. Reads "
        "DJANGO_SUPERUSER_USERNAME (default: admin), DJANGO_SUPERUSER_EMAIL and "
        "DJANGO_SUPERUSER_PASSWORD. Without a password, one is generated and "
        "printed."
    )

    def handle(self, *args, **options):
        user_model = get_user_model()
        if user_model.objects.filter(is_superuser=True).exists():
            return

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME") or "admin"
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        if not password:
            password = secrets.token_urlsafe(16)
            self.stdout.write(f"Generated password for {username}: {password}")

        user_model.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(f"Created superuser {username}"))
