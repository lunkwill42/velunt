from django.db.models import Max, Min
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from velunt.tasting.forms import ScorecardForm
from velunt.tasting.models import Event, Scorecard, ScorecardLine
from velunt.tasting.qr import generate_qr_svg
from velunt.tasting.scoring import get_scoring_system


def event_list(request):
    """List events the current session has scorecards for."""
    scorecard_ids = _get_all_session_scorecard_ids(request)
    scorecards = Scorecard.objects.filter(public_id__in=scorecard_ids).select_related(
        "event"
    )
    events = [sc.event for sc in scorecards]
    return render(request, "tasting/event_list.html", {"events": events})


def scorecard_list(request):
    """List scorecards tied to the current session."""
    scorecard_ids = _get_all_session_scorecard_ids(request)
    scorecards = (
        Scorecard.objects.filter(public_id__in=scorecard_ids)
        .select_related("event")
        .order_by("-event__event_date")
    )
    return render(request, "tasting/scorecard_list.html", {"scorecards": scorecards})


def event_detail(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    event_url = request.build_absolute_uri()
    qr_svg = generate_qr_svg(event_url)

    existing_scorecard = _get_session_scorecard(request, event)
    form = ScorecardForm(event=event) if event.state == "open" else None
    event_stats = _get_event_stats(event) if event.state == "closed" else None

    return render(
        request,
        "tasting/event_detail.html",
        {
            "event": event,
            "qr_svg": qr_svg,
            "existing_scorecard": existing_scorecard,
            "form": form,
            "event_stats": event_stats,
        },
    )


def create_scorecard(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if event.state != "open":
        return redirect("tasting:event_detail", public_id=event.public_id)

    form = ScorecardForm(request.POST, event=event)
    if not form.is_valid():
        event_url = request.build_absolute_uri(event.get_absolute_url())
        qr_svg = generate_qr_svg(event_url)
        return render(
            request,
            "tasting/event_detail.html",
            {
                "event": event,
                "qr_svg": qr_svg,
                "existing_scorecard": None,
                "form": form,
            },
        )

    scorecard = Scorecard.objects.create(
        event=event,
        judge_name=form.cleaned_data["judge_name"],
    )
    request.session[event.public_id] = scorecard.public_id
    return redirect("tasting:scorecard_detail", public_id=scorecard.public_id)


def scorecard_detail(request, public_id):
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    scoring_system = get_scoring_system(scorecard.event.scoring_system)
    lines = scorecard.lines.all()
    next_beer_number = _next_beer_number(lines)

    return render(
        request,
        "tasting/scorecard_detail.html",
        {
            "scorecard": scorecard,
            "scoring_system": scoring_system,
            "lines": lines,
            "next_beer_number": next_beer_number,
        },
    )


def save_score_line(request, public_id):
    """Create or update a score line via HTMX POST."""
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    scoring_system = get_scoring_system(scorecard.event.scoring_system)

    if scorecard.event.state != "open":
        beer_number = request.POST.get("beer_number")
        line = ScorecardLine.objects.filter(
            scorecard=scorecard, beer_number=beer_number
        ).first()
        if line:
            return render(
                request,
                "tasting/_score_line.html",
                {
                    "line": line,
                    "scorecard": scorecard,
                    "scoring_system": scoring_system,
                    "readonly": True,
                    "keep_open": True,
                    "closed_message": (
                        "Arrangementet er avsluttet. Endringer er ikke lenger mulig."
                    ),
                },
            )
        return HttpResponse("Arrangementet er lukket.", status=403)

    beer_number = request.POST.get("beer_number")
    if not beer_number:
        return HttpResponse("Ølnummer mangler.", status=400)

    try:
        beer_number = int(beer_number)
    except ValueError:
        return HttpResponse("Ugyldig ølnummer.", status=400)

    line, _created = ScorecardLine.objects.get_or_create(
        scorecard=scorecard,
        beer_number=beer_number,
    )

    scores = {}
    for dim in scoring_system.dimensions:
        value = request.POST.get(dim.key)
        if value:
            scores[dim.key] = value
    line.scores = scores
    line.comment = request.POST.get("comment", "")
    line.save()

    return render(
        request,
        "tasting/_score_line.html",
        {
            "line": line,
            "scorecard": scorecard,
            "scoring_system": scoring_system,
            "keep_open": True,
        },
    )


def add_score_line(request, public_id):
    """Add a new score line and return all lines (full re-render)."""
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if scorecard.event.state != "open":
        return HttpResponse("Arrangementet er lukket.", status=403)

    beer_number = request.POST.get("beer_number")
    if not beer_number:
        return HttpResponse("Ølnummer mangler.", status=400)
    try:
        beer_number = int(beer_number)
    except ValueError:
        return HttpResponse("Ugyldig ølnummer.", status=400)

    scoring_system = get_scoring_system(scorecard.event.scoring_system)
    error = None

    if ScorecardLine.objects.filter(
        scorecard=scorecard, beer_number=beer_number
    ).exists():
        error = f"Øl #{beer_number} er allerede lagt til."
    else:
        ScorecardLine.objects.create(scorecard=scorecard, beer_number=beer_number)

    lines = scorecard.lines.all()
    next_beer = _next_beer_number(lines)

    return render(
        request,
        "tasting/_score_lines.html",
        {
            "lines": lines,
            "scorecard": scorecard,
            "scoring_system": scoring_system,
            "next_beer_number": next_beer,
            "add_error": error,
        },
    )


def delete_score_line(request, public_id, beer_number):
    """Delete a score line and return all lines (full re-render)."""
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    if scorecard.event.state != "open":
        return HttpResponse("Arrangementet er lukket.", status=403)

    ScorecardLine.objects.filter(scorecard=scorecard, beer_number=beer_number).delete()

    scoring_system = get_scoring_system(scorecard.event.scoring_system)
    lines = scorecard.lines.all()
    next_beer = _next_beer_number(lines)

    return render(
        request,
        "tasting/_score_lines.html",
        {
            "lines": lines,
            "scorecard": scorecard,
            "scoring_system": scoring_system,
            "next_beer_number": next_beer,
        },
    )


def confirm_delete_line(request, public_id, beer_number):
    """Return the delete confirmation partial."""
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    return render(
        request,
        "tasting/_confirm_delete.html",
        {"scorecard": scorecard, "beer_number": beer_number},
    )


def cancel_delete_line(request, public_id, beer_number):
    """Return the delete button partial (restores after cancel)."""
    scorecard = get_object_or_404(
        Scorecard.objects.select_related("event"), public_id=public_id
    )
    return render(
        request,
        "tasting/_delete_button.html",
        {"scorecard": scorecard, "beer_number": beer_number},
    )


def _get_session_scorecard(request, event):
    """Look up an existing scorecard from the session."""
    scorecard_id = request.session.get(event.public_id)
    if not scorecard_id:
        return None
    return Scorecard.objects.filter(public_id=scorecard_id, event=event).first()


def _next_beer_number(lines):
    """Suggest the next beer number after the highest used."""
    if not lines:
        return 1
    return max(line.beer_number for line in lines) + 1


def _get_all_session_scorecard_ids(request):
    """Extract all scorecard public_ids stored in the session."""
    return [v for k, v in request.session.items() if isinstance(v, str) and len(v) == 6]


def _get_event_stats(event):
    """Compute summary statistics for a closed event."""
    lines = ScorecardLine.objects.filter(scorecard__event=event)
    timestamps = lines.aggregate(
        first_score_at=Min("created_at"),
        last_score_at=Max("updated_at"),
    )
    return {
        "scorecard_count": event.scorecards.count(),
        "beer_count": lines.values("beer_number").distinct().count(),
        "first_score_at": timestamps["first_score_at"],
        "last_score_at": timestamps["last_score_at"],
    }
