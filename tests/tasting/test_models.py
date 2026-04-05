import datetime
from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.utils import timezone

from velunt.tasting.models import (
    AnswerKey,
    AnswerKeyEntry,
    Beer,
    Event,
    Scorecard,
    ScorecardLine,
)


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


class TestEventState:
    def test_when_event_date_is_future_state_should_be_not_yet_open(self, make_event):
        event = make_event(
            event_date=datetime.date.today() + datetime.timedelta(days=7)
        )
        assert event.state == "not_yet_open"

    def test_when_event_date_is_today_and_not_closed_state_should_be_open(
        self, make_event
    ):  # noqa: E501
        event = make_event(event_date=datetime.date.today())
        assert event.state == "open"

    def test_when_event_date_is_past_and_not_closed_state_should_be_open(
        self, make_event
    ):  # noqa: E501
        event = make_event(
            event_date=datetime.date.today() - datetime.timedelta(days=1)
        )
        assert event.state == "open"

    def test_when_closed_at_is_set_state_should_be_closed(self, make_event):
        event = make_event(closed_at=timezone.now())
        assert event.state == "closed"

    def test_when_closed_at_set_for_future_event_state_should_be_closed(
        self, make_event
    ):  # noqa: E501
        event = make_event(
            event_date=datetime.date.today() + datetime.timedelta(days=7),
            closed_at=timezone.now(),
        )
        assert event.state == "closed"


class TestEventPublicId:
    def test_when_created_it_should_have_a_6_char_public_id(self, make_event):
        event = make_event()
        assert len(event.public_id) == 6

    def test_when_two_events_created_they_should_have_different_ids(self, make_event):
        event1 = make_event(description="Smak 1")
        event2 = make_event(description="Smak 2")
        assert event1.public_id != event2.public_id


class TestEventStr:
    def test_when_converted_to_string_it_should_return_description(self, make_event):
        event = make_event(description="Juleølsmaking 2026")
        assert str(event) == "Juleølsmaking 2026"


class TestScorecard:
    def test_when_created_it_should_have_a_6_char_public_id(self, make_event):
        event = make_event()
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        assert len(scorecard.public_id) == 6

    def test_when_converted_to_string_it_should_return_judge_name(self, make_event):
        event = make_event()
        scorecard = Scorecard.objects.create(event=event, judge_name="Morten")
        assert str(scorecard) == "Morten"

    def test_when_duplicate_name_in_same_event_it_should_raise(self, make_event):
        event = make_event()
        Scorecard.objects.create(event=event, judge_name="Morten")
        with pytest.raises(IntegrityError):
            Scorecard.objects.create(event=event, judge_name="Morten")

    def test_when_same_name_in_different_events_it_should_succeed(self, make_event):
        event1 = make_event(description="Smak 1")
        event2 = make_event(description="Smak 2")
        Scorecard.objects.create(event=event1, judge_name="Morten")
        scorecard2 = Scorecard.objects.create(event=event2, judge_name="Morten")
        assert scorecard2.pk is not None


@pytest.fixture()
def scorecard(make_event):
    event = make_event()
    return Scorecard.objects.create(event=event, judge_name="Morten")


class TestScorecardLine:
    def test_when_all_scores_present_save_should_compute_total(self, scorecard):
        line = ScorecardLine.objects.create(
            scorecard=scorecard,
            beer_number=1,
            scores={"untappd": "3.5", "julete": "4.0"},
        )
        assert line.total_score == Decimal("14.00")

    def test_when_scores_incomplete_total_should_be_none(self, scorecard):
        line = ScorecardLine.objects.create(
            scorecard=scorecard,
            beer_number=1,
            scores={"untappd": "3.5"},
        )
        assert line.total_score is None

    def test_when_scores_empty_total_should_be_none(self, scorecard):
        line = ScorecardLine.objects.create(
            scorecard=scorecard,
            beer_number=1,
            scores={},
        )
        assert line.total_score is None

    def test_when_scores_updated_save_should_recompute_total(self, scorecard):
        line = ScorecardLine.objects.create(
            scorecard=scorecard,
            beer_number=1,
            scores={"untappd": "3.5", "julete": "4.0"},
        )
        assert line.total_score == Decimal("14.00")
        line.scores = {"untappd": "5.0", "julete": "5.0"}
        line.save()
        assert line.total_score == Decimal("25.00")

    def test_when_converted_to_string_it_should_show_beer_number(self, scorecard):
        line = ScorecardLine(scorecard=scorecard, beer_number=3)
        assert str(line) == "Øl #3"


class TestBeer:
    def test_when_converted_to_string_it_should_return_name(self, make_event):
        event = make_event()
        beer = Beer.objects.create(event=event, name="Nøgne Ø Julefest")
        assert str(beer) == "Nøgne Ø Julefest"


class TestAnswerKey:
    @pytest.fixture()
    def answer_key(self, make_event, user):
        event = make_event()
        return AnswerKey.objects.create(event=event, created_by=user)

    def test_when_published_at_is_null_is_published_should_be_false(self, answer_key):
        assert answer_key.is_published is False

    def test_when_published_at_is_in_past_is_published_should_be_true(self, answer_key):
        answer_key.published_at = timezone.now() - datetime.timedelta(hours=1)
        answer_key.save()
        assert answer_key.is_published is True

    def test_when_published_at_is_in_future_is_published_should_be_false(
        self, answer_key
    ):
        answer_key.published_at = timezone.now() + datetime.timedelta(hours=1)
        answer_key.save()
        assert answer_key.is_published is False


class TestAnswerKeyEntry:
    def test_when_same_beer_number_twice_it_should_raise(self, make_event, user):
        event = make_event()
        ak = AnswerKey.objects.create(event=event, created_by=user)
        beer = Beer.objects.create(event=event, name="Testøl")
        AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer)
        with pytest.raises(IntegrityError):
            AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer)

    def test_when_same_beer_different_numbers_it_should_succeed(self, make_event, user):
        event = make_event()
        ak = AnswerKey.objects.create(event=event, created_by=user)
        beer = Beer.objects.create(event=event, name="Kontrolløl")
        AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer)
        entry2 = AnswerKeyEntry.objects.create(answer_key=ak, beer_number=5, beer=beer)
        assert entry2.pk is not None

    def test_when_converted_to_string_it_should_show_number_and_name(
        self, make_event, user
    ):
        event = make_event()
        ak = AnswerKey.objects.create(event=event, created_by=user)
        beer = Beer.objects.create(event=event, name="Nøgne Ø Julefest")
        entry = AnswerKeyEntry.objects.create(answer_key=ak, beer_number=3, beer=beer)
        assert str(entry) == "#3: Nøgne Ø Julefest"
