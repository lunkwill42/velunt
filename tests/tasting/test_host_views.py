import pytest

from velunt.tasting.models import AnswerKey, AnswerKeyEntry, Beer
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


@pytest.fixture()
def event(make_event):
    return make_event(host_token=generate_host_token())


def host_url(event, suffix=""):
    return f"/host/{event.host_token}/{suffix}"
