from django.urls import path

from velunt.tasting import views

app_name = "tasting"

urlpatterns = [
    path("event/", views.event_list, name="event_list"),
    path("scorecard/", views.scorecard_list, name="scorecard_list"),
    path("event/<str:public_id>/", views.event_detail, name="event_detail"),
    path(
        "event/<str:public_id>/create-scorecard/",
        views.create_scorecard,
        name="create_scorecard",
    ),
    path(
        "scorecard/<str:public_id>/",
        views.scorecard_detail,
        name="scorecard_detail",
    ),
    path(
        "scorecard/<str:public_id>/save-line/",
        views.save_score_line,
        name="save_score_line",
    ),
    path(
        "scorecard/<str:public_id>/add-line/",
        views.add_score_line,
        name="add_score_line",
    ),
    path(
        "scorecard/<str:public_id>/delete-line/<int:beer_number>/",
        views.delete_score_line,
        name="delete_score_line",
    ),
    path(
        "scorecard/<str:public_id>/confirm-delete/<int:beer_number>/",
        views.confirm_delete_line,
        name="confirm_delete_line",
    ),
    path(
        "scorecard/<str:public_id>/cancel-delete/<int:beer_number>/",
        views.cancel_delete_line,
        name="cancel_delete_line",
    ),
]
