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
            change_url(answer_key), answer_key_form_data(answer_key.event, [other_beer])
        )

        assert response.status_code == 200
        assert not answer_key.entries.exists()
        assert "beer" in entry_errors(response)[0]

    def test_when_saving_a_beer_from_the_same_event_it_should_add_the_entry(
        self, admin_client, answer_key
    ):  # noqa: E501
        beer = Beer.objects.create(event=answer_key.event, name="Underlig Jul")

        response = admin_client.post(
            change_url(answer_key), answer_key_form_data(answer_key.event, [beer])
        )

        assert response.status_code == 302
        assert answer_key.entries.get().beer == beer

    def test_when_editing_it_should_not_allow_changing_the_event(
        self, admin_client, answer_key, make_event
    ):  # noqa: E501
        original_event = answer_key.event
        data = answer_key_form_data(answer_key.event)
        data["event"] = make_event().pk

        response = admin_client.post(change_url(answer_key), data)

        assert response.status_code == 302
        answer_key.refresh_from_db()
        assert answer_key.event == original_event


class TestAnswerKeyAddPage:
    def test_when_event_is_unknown_it_should_not_offer_entries_yet(self, admin_client):  # noqa: E501
        content = admin_client.get("/admin/tasting/answerkey/add/").content.decode()
        assert "entries-TOTAL_FORMS" not in content

    def test_when_opened_for_an_event_it_should_offer_that_events_beers(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()
        Beer.objects.create(event=event, name="Underlig Jul")
        Beer.objects.create(event=make_event(), name="Fremmed Julebokk")

        content = admin_client.get(add_url(event)).content.decode()

        assert "entries-TOTAL_FORMS" in content
        assert "Underlig Jul" in content
        assert "Fremmed Julebokk" not in content

    def test_when_opened_for_an_event_it_should_only_offer_that_event(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event(description="Juleølsmaking")
        make_event(description="Påskeølsmaking")

        content = admin_client.get(add_url(event)).content.decode()

        assert "Juleølsmaking" in content
        assert "Påskeølsmaking" not in content

    def test_when_saved_with_entries_it_should_create_answer_key_and_entries(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()
        beer = Beer.objects.create(event=event, name="Underlig Jul")

        response = admin_client.post(
            add_url(event), answer_key_form_data(event, [beer])
        )

        assert response.status_code == 302
        assert event.answer_key.entries.get().beer == beer

    def test_when_another_event_is_chosen_than_opened_for_it_should_reject_it(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        data = answer_key_form_data(event, [beer])
        data["event"] = make_event().pk

        response = admin_client.post(add_url(event), data)

        assert response.status_code == 200
        assert not AnswerKey.objects.exists()
        assert "event" in response.context["adminform"].form.errors

    def test_when_saved_without_known_event_it_should_create_answer_key_only(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()
        data = {
            key: value
            for key, value in answer_key_form_data(event).items()
            if not key.startswith("entries-")
        }

        response = admin_client.post("/admin/tasting/answerkey/add/", data)

        assert response.status_code == 302
        assert not event.answer_key.entries.exists()

    @pytest.mark.parametrize("event_id", ["tull", "²", "-1"])
    def test_when_event_id_is_garbage_it_should_not_offer_entries(
        self, admin_client, event_id
    ):  # noqa: E501
        response = admin_client.get(f"/admin/tasting/answerkey/add/?event={event_id}")

        assert response.status_code == 200
        assert "entries-TOTAL_FORMS" not in response.content.decode()


@pytest.fixture()
def answer_key(make_event, user):
    return AnswerKey.objects.create(event=make_event(), created_by=user)


def change_page(client, answer_key):
    return client.get(change_url(answer_key)).content.decode()


def change_url(answer_key):
    return f"/admin/tasting/answerkey/{answer_key.pk}/change/"


def add_url(event):
    return f"/admin/tasting/answerkey/add/?event={event.pk}"


def answer_key_form_data(event, beers=()):
    data = {
        "event": event.pk,
        "published_at_0": "",
        "published_at_1": "",
        "entries-TOTAL_FORMS": str(len(beers)),
        "entries-INITIAL_FORMS": "0",
        "entries-MIN_NUM_FORMS": "0",
        "entries-MAX_NUM_FORMS": "1000",
    }
    for index, beer in enumerate(beers):
        data[f"entries-{index}-beer_number"] = str(index + 1)
        data[f"entries-{index}-beer"] = beer.pk
    return data


def entry_errors(response):
    return response.context["inline_admin_formsets"][0].formset.errors
