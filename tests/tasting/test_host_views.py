import pytest
from django.utils import timezone

from velunt.tasting.models import AnswerKey, AnswerKeyEntry, Beer, Scorecard
from velunt.tasting.utils import generate_host_token

BEER_LIST = "Navn\tHjemmebrygg\tUntappd\nUnderlig Jul\t\thttps://untappd.com/b/1\n"


class TestHostBeerListView:
    def test_when_token_is_unknown_it_should_return_404(self, client, db):
        response = client.get("/host/finnes-ikke/")
        assert response.status_code == 404

    def test_when_token_is_valid_it_should_show_the_event(self, client, event):
        response = client.get(host_url(event))
        assert response.status_code == 200
        assert "Testsmak" in response.content.decode()

    def test_when_event_has_beers_it_should_list_them(self, client, event):
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        beer.links.create(label="Untappd", url="https://untappd.com/b/1")

        content = client.get(host_url(event)).content.decode()

        assert "Underlig Jul" in content
        assert "https://untappd.com/b/1" in content


class TestPreviewBeerImportView:
    def test_when_rows_are_posted_it_should_show_them_without_saving(
        self, client, event
    ):  # noqa: E501
        response = client.post(host_url(event, "preview/"), {"beer_list": BEER_LIST})

        assert "Underlig Jul" in response.content.decode()
        assert not event.beers.exists()

    def test_when_no_beers_are_found_it_should_say_so(self, client, event):
        response = client.post(host_url(event, "preview/"), {"beer_list": "Navn"})
        assert "Fant ingen øl" in response.content.decode()

    def test_when_using_get_it_should_return_405(self, client, event):
        response = client.get(host_url(event, "preview/"))
        assert response.status_code == 405


class TestImportBeersView:
    def test_when_rows_are_posted_it_should_save_beers_and_redirect_back(
        self, client, event
    ):  # noqa: E501
        response = client.post(host_url(event, "import/"), {"beer_list": BEER_LIST})

        assert response.status_code == 302
        assert response.url == host_url(event)
        beer = event.beers.get()
        assert beer.name == "Underlig Jul"
        assert beer.links.get().url == "https://untappd.com/b/1"

    def test_when_import_is_done_it_should_report_what_changed(self, client, event):
        response = client.post(
            host_url(event, "import/"), {"beer_list": BEER_LIST}, follow=True
        )
        assert "La til 1 øl" in response.content.decode()

    def test_when_replace_is_checked_it_should_remove_beers_not_listed(
        self, client, event
    ):  # noqa: E501
        Beer.objects.create(event=event, name="Julebokk")

        client.post(
            host_url(event, "import/"), {"beer_list": BEER_LIST, "replace": "on"}
        )

        assert list(event.beers.values_list("name", flat=True)) == ["Underlig Jul"]

    def test_when_replace_is_unchecked_it_should_keep_beers_not_listed(
        self, client, event
    ):  # noqa: E501
        Beer.objects.create(event=event, name="Julebokk")

        client.post(host_url(event, "import/"), {"beer_list": BEER_LIST})

        assert event.beers.count() == 2

    @pytest.mark.parametrize("pasted", ["", "Navn\tHjemmebrygg"])
    def test_when_paste_has_no_beers_it_should_not_replace_the_list(
        self, client, event, pasted
    ):  # noqa: E501
        Beer.objects.create(event=event, name="Julebokk")

        response = client.post(
            host_url(event, "import/"), {"beer_list": pasted, "replace": "on"}
        )

        assert "ingenting ble endret" in response.content.decode()
        assert list(event.beers.values_list("name", flat=True)) == ["Julebokk"]

    def test_when_paste_has_too_long_values_it_should_import_nothing(
        self, client, event
    ):  # noqa: E501
        pasted = "Navn\tUntappd\nUnderlig Jul\thttps://untappd.com/b/" + "x" * 200

        response = client.post(host_url(event, "import/"), {"beer_list": pasted})

        assert response.status_code == 200
        assert "lengre enn 200 tegn" in response.content.decode()
        assert not event.beers.exists()

    def test_when_paste_has_no_beers_it_should_keep_the_pasted_text(
        self, client, event
    ):  # noqa: E501
        response = client.post(host_url(event, "import/"), {"beer_list": "Navn"})

        assert ">Navn</textarea>" in response.content.decode()

    def test_when_using_get_it_should_return_405(self, client, event):
        response = client.get(host_url(event, "import/"))
        assert response.status_code == 405


class TestDeleteBeerView:
    def test_when_beer_is_not_in_answer_key_it_should_remove_it(self, client, event):
        beer = Beer.objects.create(event=event, name="Julebokk")

        response = client.delete(host_url(event, f"beer/{beer.pk}/"))

        assert response.status_code == 200
        assert not event.beers.exists()

    def test_when_beer_is_in_answer_key_it_should_keep_it_and_explain_why(
        self, client, event, user
    ):  # noqa: E501
        beer = Beer.objects.create(event=event, name="Julebokk")
        answer_key = AnswerKey.objects.create(event=event, created_by=user)
        AnswerKeyEntry.objects.create(answer_key=answer_key, beer_number=1, beer=beer)

        response = client.delete(host_url(event, f"beer/{beer.pk}/"))

        assert "kan ikke fjernes" in response.content.decode()
        assert event.beers.exists()

    def test_when_beer_belongs_to_another_event_it_should_return_404(
        self, client, event, make_event
    ):  # noqa: E501
        beer = Beer.objects.create(event=make_event(), name="Julebokk")

        response = client.delete(host_url(event, f"beer/{beer.pk}/"))

        assert response.status_code == 404
        assert Beer.objects.filter(pk=beer.pk).exists()

    def test_when_using_get_it_should_return_405(self, client, event):
        beer = Beer.objects.create(event=event, name="Julebokk")
        response = client.get(host_url(event, f"beer/{beer.pk}/"))
        assert response.status_code == 405


class TestLockedBeerList:
    def test_when_locked_it_should_not_offer_import(self, client, locked_event):
        content = client.get(host_url(locked_event)).content.decode()
        assert "Importer øl" not in content
        assert "kan ikke lenger endres" in content

    def test_when_locked_it_should_refuse_import(self, client, locked_event):
        response = client.post(
            host_url(locked_event, "import/"), {"beer_list": BEER_LIST}
        )

        assert response.status_code == 403
        assert not locked_event.beers.exists()

    def test_when_locked_it_should_refuse_removing_beers(self, client, locked_event):
        beer = Beer.objects.create(event=locked_event, name="Julebokk")

        response = client.delete(host_url(locked_event, f"beer/{beer.pk}/"))

        assert response.status_code == 403
        assert locked_event.beers.exists()


class TestHostAnswerKeyView:
    def test_when_judges_scored_numbers_it_should_list_one_row_per_number(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2, 3])
        add_scorecard(event, "Kari", [1, 3])

        rows = client.get(answer_key_url(event)).context["edit"].rows

        assert [row.beer_number for row in rows] == [1, 2, 3]

    def test_when_number_is_on_few_scorecards_it_should_name_the_judges(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 21])
        add_scorecard(event, "Kari", [1])
        add_scorecard(event, "Per", [1])

        content = client.get(answer_key_url(event)).content.decode()

        assert "Bare hos Ola." in content

    def test_when_a_scorecard_is_empty_it_should_not_count_as_a_judge(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1])
        add_scorecard(event, "Kari", [1])
        add_scorecard(event, "Ola 2", [])

        row = client.get(answer_key_url(event)).context["edit"].rows[0]

        assert row.is_on_all_scorecards

    def test_when_beers_are_named_it_should_save_them_in_the_answer_key(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2])
        raudt = Beer.objects.create(event=event, name="Raudt Juleøl")
        jul = Beer.objects.create(event=event, name="Underlig Jul")

        response = client.post(
            answer_key_url(event), {"beer_1": "raudt juleøl", "beer_2": "Underlig Jul"}
        )

        assert response.status_code == 302
        assert answer_key_map(event) == {1: raudt, 2: jul}

    def test_when_new_answer_key_is_saved_it_should_credit_the_event_owner(
        self, client, event, user
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1])
        Beer.objects.create(event=event, name="Underlig Jul")

        client.post(answer_key_url(event), {"beer_1": "Underlig Jul"})

        assert event.answer_key.created_by == user

    def test_when_row_is_empty_it_should_leave_the_number_out(self, client, event):
        add_scorecard(event, "Ola", [1, 21])
        beer = Beer.objects.create(event=event, name="Underlig Jul")

        client.post(answer_key_url(event), {"beer_1": "Underlig Jul", "beer_21": ""})

        assert answer_key_map(event) == {1: beer}

    def test_when_beer_is_served_twice_it_should_accept_it_on_both_numbers(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2])
        beer = Beer.objects.create(event=event, name="Underlig Jul")

        client.post(
            answer_key_url(event), {"beer_1": "Underlig Jul", "beer_2": "Underlig Jul"}
        )

        assert answer_key_map(event) == {1: beer, 2: beer}

    def test_when_a_beer_is_unknown_it_should_save_nothing_and_say_why(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2])
        Beer.objects.create(event=event, name="Underlig Jul")

        response = client.post(
            answer_key_url(event), {"beer_1": "Underlig Jul", "beer_2": "Raudt"}
        )

        assert response.status_code == 422
        assert "Fant ikke «Raudt» på øllisten." in response.content.decode()
        assert not AnswerKey.objects.filter(event=event).exists()

    def test_when_a_beer_is_unknown_it_should_keep_the_saved_answer_key(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2])
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        add_answer_key_entry(event, 1, beer)

        client.post(answer_key_url(event), {"beer_1": "", "beer_2": "Raudt"})

        assert answer_key_map(event) == {1: beer}

    def test_when_beer_is_on_several_numbers_it_should_name_the_others(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2, 3])
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        for number in (1, 3):
            add_answer_key_entry(event, number, beer)

        content = client.get(answer_key_url(event)).content.decode()

        assert "Samme øl som #3." in content
        assert "Samme øl som #1." in content

    def test_when_other_events_have_scorecards_it_should_not_list_their_numbers(
        self, client, event, make_event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1])
        add_scorecard(make_event(description="Annen smak"), "Kari", [2])

        rows = client.get(answer_key_url(event)).context["edit"].rows

        assert [row.beer_number for row in rows] == [1]

    def test_when_beer_belongs_to_another_event_it_should_reject_it(
        self, client, event, make_event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1])
        Beer.objects.create(event=make_event(), name="Underlig Jul")

        response = client.post(answer_key_url(event), {"beer_1": "Underlig Jul"})

        assert response.status_code == 422
        assert answer_key_map(event) == {}

    def test_when_beers_are_unknown_it_should_focus_the_first_of_them(
        self, client, event
    ):  # noqa: E501
        add_scorecard(event, "Ola", [1, 2, 3])
        Beer.objects.create(event=event, name="Underlig Jul")

        response = client.post(
            answer_key_url(event),
            {"beer_1": "Underlig Jul", "beer_2": "Raudt", "beer_3": "Kinn"},
        )

        assert response.context["edit"].first_error_number == 2

    def test_when_number_is_cleared_it_should_remove_its_entry(self, client, event):
        add_scorecard(event, "Ola", [1])
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        add_answer_key_entry(event, 1, beer)

        client.post(answer_key_url(event), {"beer_1": ""})

        assert answer_key_map(event) == {}

    def test_when_number_is_only_in_the_answer_key_it_should_still_be_listed(
        self, client, event
    ):  # noqa: E501
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        add_answer_key_entry(event, 7, beer)

        rows = client.get(answer_key_url(event)).context["edit"].rows

        assert [(row.beer_number, row.beer_name) for row in rows] == [
            (7, "Underlig Jul")
        ]

    def test_when_beer_has_no_number_it_should_be_listed_as_unnumbered(
        self, client, event
    ):  # noqa: E501
        Beer.objects.create(event=event, name="Underlig Jul")

        response = client.get(answer_key_url(event))

        assert [beer.name for beer in response.context["unnumbered_beers"]] == [
            "Underlig Jul"
        ]

    def test_when_locked_it_should_show_why_and_disable_the_form(
        self, client, locked_event
    ):  # noqa: E501
        add_scorecard(locked_event, "Ola", [1])

        content = client.get(answer_key_url(locked_event)).content.decode()

        assert "fasiten kan ikke endres her" in content
        assert "<fieldset disabled>" in content

    def test_when_locked_it_should_refuse_saving(self, client, locked_event):
        add_scorecard(locked_event, "Ola", [1])
        Beer.objects.create(event=locked_event, name="Underlig Jul")

        response = client.post(answer_key_url(locked_event), {"beer_1": "Underlig Jul"})

        assert response.status_code == 403
        assert not locked_event.answer_key.entries.exists()


@pytest.fixture()
def locked_event(event, user):
    event.closed_at = timezone.now()
    event.save()
    AnswerKey.objects.create(event=event, created_by=user, published_at=timezone.now())
    return event


@pytest.fixture()
def event(make_event):
    return make_event(host_token=generate_host_token())


def host_url(event, suffix=""):
    return f"/host/{event.host_token}/{suffix}"


def answer_key_url(event):
    return host_url(event, "fasit/")


def add_scorecard(event, judge_name, beer_numbers):
    scorecard = Scorecard.objects.create(event=event, judge_name=judge_name)
    for beer_number in beer_numbers:
        scorecard.lines.create(beer_number=beer_number)


def add_answer_key_entry(event, beer_number, beer):
    answer_key, _ = AnswerKey.objects.get_or_create(
        event=event, defaults={"created_by": event.owner}
    )
    answer_key.entries.create(beer_number=beer_number, beer=beer)


def answer_key_map(event):
    entries = AnswerKeyEntry.objects.filter(answer_key__event=event)
    return {entry.beer_number: entry.beer for entry in entries}
