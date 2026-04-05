from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path(
        "admin/password_reset/",
        auth_views.PasswordResetView.as_view(),
        name="admin_password_reset",
    ),
    path("admin/", admin.site.urls),
    path("account/", include("django.contrib.auth.urls")),
    path("", include("velunt.tasting.urls")),
]
