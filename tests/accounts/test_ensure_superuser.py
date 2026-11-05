from io import StringIO

import pytest
from django.core.management import call_command

from velunt.accounts.models import User


@pytest.mark.django_db
class TestEnsureSuperuser:
    def test_when_no_superuser_exists_it_should_create_one_from_environment(
        self, monkeypatch
    ):  # noqa: E501
        monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "morten")
        monkeypatch.setenv("DJANGO_SUPERUSER_EMAIL", "morten@example.org")
        monkeypatch.setenv("DJANGO_SUPERUSER_PASSWORD", "hemmelig-passord")

        ensure_superuser()

        user = User.objects.get(username="morten")
        assert user.is_superuser
        assert user.email == "morten@example.org"
        assert user.check_password("hemmelig-passord")

    def test_when_superuser_exists_it_should_not_create_another(self, monkeypatch):
        User.objects.create_superuser("existing", "", "passord")
        monkeypatch.setenv("DJANGO_SUPERUSER_USERNAME", "morten")

        ensure_superuser()

        assert User.objects.filter(is_superuser=True).count() == 1
        assert not User.objects.filter(username="morten").exists()

    def test_when_only_regular_users_exist_it_should_create_superuser(self):
        User.objects.create_user("regular", "", "passord")

        ensure_superuser()

        assert User.objects.filter(is_superuser=True).exists()

    def test_when_username_is_not_set_it_should_default_to_admin(self):
        ensure_superuser()

        assert User.objects.get(username="admin").is_superuser

    def test_when_password_is_not_set_it_should_print_a_working_generated_password(
        self,
    ):  # noqa: E501
        output = ensure_superuser()

        password = output.splitlines()[0].rsplit(": ", 1)[1]
        assert User.objects.get(username="admin").check_password(password)


@pytest.fixture(autouse=True)
def clean_superuser_environment(monkeypatch):
    for name in (
        "DJANGO_SUPERUSER_USERNAME",
        "DJANGO_SUPERUSER_EMAIL",
        "DJANGO_SUPERUSER_PASSWORD",
    ):
        monkeypatch.delenv(name, raising=False)


def ensure_superuser():
    output = StringIO()
    call_command("ensure_superuser", stdout=output)
    return output.getvalue()
