from django.urls import path

from velunt.tasting import views

app_name = "tasting"

urlpatterns = [
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
]
