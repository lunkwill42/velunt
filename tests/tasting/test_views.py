import datetime

import pytest
from django.utils import timezone

from velunt.tasting.models import Event, Scorecard, ScorecardLine


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
        response = client.get(f"/event/{event.public_id}/")
        assert response.status_code == 200

    def test_when_event_not_found_it_should_return_404(self, client, db):
        response = client.get("/event/XXXXXX/")
        assert response.status_code == 404

    def test_when_event_is_open_it_should_show_open_status(self, client, make_event):
        event = make_event()
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "Åpent for registrering" in content

    def test_when_event_is_not_yet_open_it_should_show_not_started(
        self, client, make_event
    ):
        event = make_event(
            event_date=datetime.date.today() + datetime.timedelta(days=7)
        )
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "ikke startet" in content

    def test_when_event_is_closed_it_should_show_closed_status(
        self, client, make_event
    ):
        event = make_event(closed_at=timezone.now())
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "Avsluttet" in content

    def test_when_event_page_rendered_it_should_contain_qr_svg(
        self, client, make_event
    ):
        event = make_event()
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "<svg" in content

    def test_when_event_page_rendered_it_should_show_description(
        self, client, make_event
    ):
        event = make_event(description="Juleølsmaking 2026")
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "Juleølsmaking 2026" in content

    def test_when_session_has_scorecard_it_should_show_continue_link(
        self, client, make_event
    ):
        event = make_event()
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        session = client.session
        session[event.public_id] = scorecard.public_id
        session.save()
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "Fortsett ditt dommerskjema" in content

    def test_when_open_and_no_session_it_should_show_name_form(
        self, client, make_event
    ):
        event = make_event()
        response = client.get(f"/event/{event.public_id}/")
        content = response.content.decode()
        assert "Opprett dommerskjema" in content


class TestCreateScorecardView:
    def test_when_posting_valid_name_it_should_create_scorecard(
        self, client, make_event
    ):
        event = make_event()
        response = client.post(
            f"/event/{event.public_id}/create-scorecard/",
            {"judge_name": "Morten"},
        )
        assert Scorecard.objects.filter(event=event, judge_name="Morten").exists()
        scorecard = Scorecard.objects.get(event=event, judge_name="Morten")
        assert response.status_code == 302
        assert f"/scorecard/{scorecard.public_id}/" in response.url

    def test_when_posting_valid_name_it_should_store_in_session(
        self, client, make_event
    ):
        event = make_event()
        client.post(
            f"/event/{event.public_id}/create-scorecard/",
            {"judge_name": "Morten"},
        )
        scorecard = Scorecard.objects.get(event=event, judge_name="Morten")
        assert client.session[event.public_id] == scorecard.public_id

    def test_when_posting_duplicate_name_it_should_show_error(self, client, make_event):
        event = make_event()
        Scorecard.objects.create(event=event, judge_name="Morten")
        response = client.post(
            f"/event/{event.public_id}/create-scorecard/",
            {"judge_name": "Morten"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "allerede i bruk" in content

    def test_when_event_is_closed_it_should_redirect_to_event_page(
        self, client, make_event
    ):
        event = make_event(closed_at=timezone.now())
        response = client.post(
            f"/event/{event.public_id}/create-scorecard/",
            {"judge_name": "Morten"},
        )
        assert response.status_code == 302
        assert f"/event/{event.public_id}/" in response.url
        assert not Scorecard.objects.filter(event=event).exists()

    def test_when_using_get_it_should_return_405(self, client, make_event):
        event = make_event()
        response = client.get(f"/event/{event.public_id}/create-scorecard/")
        assert response.status_code == 405


class TestScorecardDetailView:
    def test_when_scorecard_exists_it_should_return_200(self, client, make_event):
        event = make_event()
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        response = client.get(f"/scorecard/{scorecard.public_id}/")
        assert response.status_code == 200

    def test_when_scorecard_not_found_it_should_return_404(self, client, db):
        response = client.get("/scorecard/XXXXXX/")
        assert response.status_code == 404

    def test_when_rendered_it_should_show_judge_name(self, client, make_event):
        event = make_event()
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        response = client.get(f"/scorecard/{scorecard.public_id}/")
        content = response.content.decode()
        assert "Morten" in content


class TestSaveScoreLineView:
    @pytest.fixture()
    def scorecard(self, make_event):
        event = make_event()
        return Scorecard.objects.create(event=event, judge_name="Morten")

    def test_when_posting_new_beer_it_should_create_line(self, client, scorecard):
        response = client.post(
            f"/scorecard/{scorecard.public_id}/save-line/",
            {"beer_number": "1", "untappd": "3.5", "julete": "4.0", "comment": "God"},
        )
        assert response.status_code == 200
        line = ScorecardLine.objects.get(scorecard=scorecard, beer_number=1)
        assert line.scores["untappd"] == "3.5"
        assert line.comment == "God"

    def test_when_posting_existing_beer_it_should_update_line(self, client, scorecard):
        ScorecardLine.objects.create(
            scorecard=scorecard, beer_number=1, scores={"untappd": "2.0"}
        )
        client.post(
            f"/scorecard/{scorecard.public_id}/save-line/",
            {"beer_number": "1", "untappd": "3.5", "julete": "4.0"},
        )
        line = ScorecardLine.objects.get(scorecard=scorecard, beer_number=1)
        assert line.scores["untappd"] == "3.5"
        assert line.scores["julete"] == "4.0"

    def test_when_event_is_closed_it_should_return_403(self, client, make_event):
        event = make_event(closed_at=timezone.now())
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        response = client.post(
            f"/scorecard/{scorecard.public_id}/save-line/",
            {"beer_number": "1", "untappd": "3.5", "julete": "4.0"},
        )
        assert response.status_code == 403

    def test_when_response_returned_it_should_be_html_partial(self, client, scorecard):
        response = client.post(
            f"/scorecard/{scorecard.public_id}/save-line/",
            {"beer_number": "1"},
        )
        content = response.content.decode()
        assert "Øl #1" in content

    def test_when_using_get_it_should_return_405(self, client, scorecard):
        response = client.get(f"/scorecard/{scorecard.public_id}/save-line/")
        assert response.status_code == 405
