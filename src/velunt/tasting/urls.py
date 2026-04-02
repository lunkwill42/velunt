from django.urls import path

from velunt.tasting import views

app_name = "tasting"

urlpatterns = [
    path("event/<str:public_id>/", views.event_detail, name="event_detail"),
]
