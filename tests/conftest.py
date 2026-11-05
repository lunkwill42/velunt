import datetime

import pytest

from velunt.accounts.models import User
from velunt.tasting.models import Event


@pytest.fixture()
def make_event(user):
    def _make_event(**kwargs):
        defaults = {
            "owner": user,
            "description": "Testsmak",
            "event_date": datetime.date.today(),
            "scoring_system": "juleol",
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    return _make_event


@pytest.fixture()
def user(db):
    return User.objects.create_user(username="testuser", password="testpass")
