import datetime

import pytest
from django.utils import timezone

from velunt.tasting.models import Event


@pytest.fixture()
def user(db):
    from velunt.accounts.models import User

    return User.objects.create_user(username="testuser", password="testpass")


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


class TestEventDetailView:
    def test_when_event_exists_it_should_return_200(self, client, make_event):
        event = make_event()
        response = client.get(f"/{event.public_id}/")
        assert response.status_code == 200

    def test_when_event_not_found_it_should_return_404(self, client, db):
        response = client.get("/XXXXXX/")
        assert response.status_code == 404

    def test_when_event_is_open_it_should_show_open_status(self, client, make_event):
        event = make_event()
        response = client.get(f"/{event.public_id}/")
        content = response.content.decode()
        assert "Åpent for registrering" in content

    def test_when_event_is_not_yet_open_it_should_show_not_started(
        self, client, make_event
    ):
        event = make_event(
            event_date=datetime.date.today() + datetime.timedelta(days=7)
        )
        response = client.get(f"/{event.public_id}/")
        content = response.content.decode()
        assert "ikke startet" in content

    def test_when_event_is_closed_it_should_show_closed_status(
        self, client, make_event
    ):
        event = make_event(closed_at=timezone.now())
        response = client.get(f"/{event.public_id}/")
        content = response.content.decode()
        assert "Avsluttet" in content

    def test_when_event_page_rendered_it_should_contain_qr_svg(
        self, client, make_event
    ):
        event = make_event()
        response = client.get(f"/{event.public_id}/")
        content = response.content.decode()
        assert "<svg" in content

    def test_when_event_page_rendered_it_should_show_description(
        self, client, make_event
    ):
        event = make_event(description="Juleølsmaking 2026")
        response = client.get(f"/{event.public_id}/")
        content = response.content.decode()
        assert "Juleølsmaking 2026" in content
