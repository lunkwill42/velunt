import django


class TestDjangoBootstrap:
    def test_when_starting_django_should_initialize_without_errors(self):
        django.setup()

    def test_when_requesting_admin_login_it_should_return_200(self, client):
        response = client.get("/admin/login/")
        assert response.status_code == 200
