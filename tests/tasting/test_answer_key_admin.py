import pytest

from velunt.tasting.models import AnswerKey, Beer


class TestAnswerKeyChangePage:
    def test_when_editing_entries_it_should_only_offer_the_events_beers(
        self, admin_client, answer_key, make_event
    ):  # noqa: E501
        Beer.objects.create(event=answer_key.event, name="Underlig Jul")
        Beer.objects.create(event=make_event(), name="Fremmed Julebokk")

        content = change_page(admin_client, answer_key)

        assert "Underlig Jul" in content
        assert "Fremmed Julebokk" not in content

    def test_when_saving_a_beer_from_another_event_it_should_reject_it(
        self, admin_client, answer_key, make_event
    ):  # noqa: E501
        other_beer = Beer.objects.create(event=make_event(), name="Fremmed Julebokk")

        response = admin_client.post(
            change_url(answer_key), entry_form_data(answer_key, other_beer)
        )

        assert response.status_code == 200
        assert not answer_key.entries.exists()
        assert "beer" in entry_errors(response)[0]

    def test_when_saving_a_beer_from_the_same_event_it_should_add_the_entry(
        self, admin_client, answer_key
    ):  # noqa: E501
        beer = Beer.objects.create(event=answer_key.event, name="Underlig Jul")

        response = admin_client.post(
            change_url(answer_key), entry_form_data(answer_key, beer)
        )

        assert response.status_code == 302
        assert answer_key.entries.get().beer == beer


class TestAnswerKeyAddPage:
    def test_when_adding_an_answer_key_it_should_not_offer_entries_yet(
        self, admin_client
    ):  # noqa: E501
        content = admin_client.get("/admin/tasting/answerkey/add/").content.decode()
        assert "entries-TOTAL_FORMS" not in content


@pytest.fixture()
def answer_key(make_event, user):
    return AnswerKey.objects.create(event=make_event(), created_by=user)


def change_page(client, answer_key):
    return client.get(change_url(answer_key)).content.decode()


def change_url(answer_key):
    return f"/admin/tasting/answerkey/{answer_key.pk}/change/"


def entry_form_data(answer_key, beer):
    return {
        "event": answer_key.event.pk,
        "published_at_0": "",
        "published_at_1": "",
        "entries-TOTAL_FORMS": "1",
        "entries-INITIAL_FORMS": "0",
        "entries-MIN_NUM_FORMS": "0",
        "entries-MAX_NUM_FORMS": "1000",
        "entries-0-beer_number": "1",
        "entries-0-beer": beer.pk,
    }


def entry_errors(response):
    return response.context["inline_admin_formsets"][0].formset.errors
