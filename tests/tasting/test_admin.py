from velunt.accounts.models import User
from velunt.tasting.models import Event


class TestRegenerateHostLinkView:
    def test_when_event_has_no_host_link_it_should_create_one(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()

        regenerate_host_link(admin_client, event)

        event.refresh_from_db()
        assert event.host_token

    def test_when_event_has_a_host_link_it_should_replace_it(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event(host_token="gammel-lenke")

        regenerate_host_link(admin_client, event)

        event.refresh_from_db()
        assert event.host_token != "gammel-lenke"

    def test_when_done_it_should_redirect_back_to_the_event(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()

        response = regenerate_host_link(admin_client, event)

        assert response.status_code == 302
        assert response.url == f"/admin/tasting/event/{event.pk}/change/"

    def test_when_using_get_it_should_not_change_the_link(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event(host_token="gammel-lenke")

        response = admin_client.get(regenerate_url(event))

        assert response.status_code == 405
        event.refresh_from_db()
        assert event.host_token == "gammel-lenke"

    def test_when_user_does_not_own_the_event_it_should_return_404(
        self, client, make_event
    ):  # noqa: E501
        event = make_event(host_token="gammel-lenke")
        client.force_login(
            User.objects.create_user("annen", password="passord", is_staff=True)
        )

        response = regenerate_host_link(client, event)

        assert response.status_code == 404
        event.refresh_from_db()
        assert event.host_token == "gammel-lenke"


class TestEventChangePage:
    def test_when_event_has_a_host_link_it_should_show_it(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event(host_token="hemmelig-lenke")

        content = change_page(admin_client, event)

        assert "/host/hemmelig-lenke/" in content
        assert "Lag ny vertskapslenke" in content

    def test_when_event_has_no_host_link_it_should_offer_to_create_one(
        self, admin_client, make_event
    ):  # noqa: E501
        event = make_event()

        content = change_page(admin_client, event)

        assert "Lag vertskapslenke" in content
        assert regenerate_url(event) in content


def regenerate_host_link(client, event: Event):
    return client.post(regenerate_url(event))


def regenerate_url(event: Event):
    return f"/admin/tasting/event/{event.pk}/regenerate-host-link/"


def change_page(client, event: Event):
    return client.get(f"/admin/tasting/event/{event.pk}/change/").content.decode()
