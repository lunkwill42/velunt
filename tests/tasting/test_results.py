import datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from velunt.tasting.models import (
    AnswerKey,
    AnswerKeyEntry,
    Beer,
    Event,
    Scorecard,
    ScorecardLine,
)
from velunt.tasting.results import compute_results


@pytest.fixture()
def user(db):
    from velunt.accounts.models import User

    return User.objects.create_user(username="testuser", password="testpass")


@pytest.fixture()
def closed_event(user):
    return Event.objects.create(
        owner=user,
        description="Testsmak",
        event_date=datetime.date.today(),
        scoring_system="juleol",
        closed_at=timezone.now(),
    )


@pytest.fixture()
def setup_event(closed_event, user):
    """Create a closed event with beers, answer key, and scorecards."""
    event = closed_event
    beer_a = Beer.objects.create(event=event, name="Øl A")
    beer_b = Beer.objects.create(event=event, name="Øl B")

    ak = AnswerKey.objects.create(
        event=event,
        created_by=user,
        published_at=timezone.now() - datetime.timedelta(hours=1),
    )
    AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer_a)
    AnswerKeyEntry.objects.create(answer_key=ak, beer_number=2, beer=beer_b)

    sc1 = Scorecard.objects.create(event=event, judge_name="Dommer 1")
    sc2 = Scorecard.objects.create(event=event, judge_name="Dommer 2")

    ScorecardLine.objects.create(
        scorecard=sc1, beer_number=1, scores={"untappd": "4.0", "julete": "4.0"}
    )
    ScorecardLine.objects.create(
        scorecard=sc1, beer_number=2, scores={"untappd": "3.0", "julete": "2.0"}
    )
    ScorecardLine.objects.create(
        scorecard=sc2, beer_number=1, scores={"untappd": "5.0", "julete": "5.0"}
    )
    ScorecardLine.objects.create(
        scorecard=sc2, beer_number=2, scores={"untappd": "2.0", "julete": "3.0"}
    )

    return event


class TestComputeResults:
    def test_when_results_computed_beers_should_be_ranked_by_score(self, setup_event):
        results = compute_results(setup_event)
        ranked = results["ranked_beers"]
        assert len(ranked) == 2
        assert ranked[0]["beer_name"] == "Øl A"
        assert ranked[1]["beer_name"] == "Øl B"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2

    def test_when_results_computed_avg_score_should_be_correct(self, setup_event):
        results = compute_results(setup_event)
        ranked = results["ranked_beers"]
        # Beer A: (4*4 + 5*5) / 2 = (16 + 25) / 2 = 20.5
        assert ranked[0]["avg_score"] == Decimal("20.5")
        # Beer B: (3*2 + 2*3) / 2 = (6 + 6) / 2 = 6
        assert ranked[1]["avg_score"] == Decimal("6")

    def test_when_results_computed_judge_count_should_be_correct(self, setup_event):
        results = compute_results(setup_event)
        ranked = results["ranked_beers"]
        assert ranked[0]["judge_count"] == 2
        assert ranked[0]["total_judges"] == 2


class TestDuplicateDetection:
    def test_when_beer_served_twice_it_should_be_marked_duplicate(
        self, closed_event, user
    ):
        event = closed_event
        beer = Beer.objects.create(event=event, name="Kontrolløl")
        ak = AnswerKey.objects.create(
            event=event,
            created_by=user,
            published_at=timezone.now() - datetime.timedelta(hours=1),
        )
        AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer)
        AnswerKeyEntry.objects.create(answer_key=ak, beer_number=5, beer=beer)

        sc = Scorecard.objects.create(event=event, judge_name="Dommer")
        ScorecardLine.objects.create(
            scorecard=sc, beer_number=1, scores={"untappd": "3.0", "julete": "3.0"}
        )
        ScorecardLine.objects.create(
            scorecard=sc, beer_number=5, scores={"untappd": "4.0", "julete": "4.0"}
        )

        results = compute_results(event)
        ranked = results["ranked_beers"]
        for entry in ranked:
            assert entry["is_duplicate"] is True
            assert entry["duplicate_group_id"] == 0


class TestOrphanedBeerNumbers:
    def test_when_beer_number_not_in_answer_key_it_should_show_unknown(
        self, closed_event, user
    ):
        event = closed_event
        AnswerKey.objects.create(
            event=event,
            created_by=user,
            published_at=timezone.now() - datetime.timedelta(hours=1),
        )

        sc = Scorecard.objects.create(event=event, judge_name="Dommer")
        ScorecardLine.objects.create(
            scorecard=sc, beer_number=99, scores={"untappd": "3.0", "julete": "3.0"}
        )

        results = compute_results(event)
        ranked = results["ranked_beers"]
        assert len(ranked) == 1
        assert ranked[0]["beer_name"] == "Ukjent øl #99"
        assert ranked[0]["beer"] is None


class TestIncompleteScoresExcluded:
    def test_when_score_incomplete_it_should_not_count(self, closed_event, user):
        event = closed_event
        beer = Beer.objects.create(event=event, name="Testøl")
        ak = AnswerKey.objects.create(
            event=event,
            created_by=user,
            published_at=timezone.now() - datetime.timedelta(hours=1),
        )
        AnswerKeyEntry.objects.create(answer_key=ak, beer_number=1, beer=beer)

        sc = Scorecard.objects.create(event=event, judge_name="Dommer")
        ScorecardLine.objects.create(
            scorecard=sc, beer_number=1, scores={"untappd": "3.0"}
        )

        results = compute_results(event)
        ranked = results["ranked_beers"]
        assert ranked[0]["judge_count"] == 0
        assert ranked[0]["avg_score"] == Decimal("0")
