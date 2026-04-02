from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from velunt.tasting.forms import ScorecardForm
from velunt.tasting.models import Event, Scorecard
from velunt.tasting.qr import generate_qr_svg


def event_detail(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    event_url = request.build_absolute_uri()
    qr_svg = generate_qr_svg(event_url)

    existing_scorecard = _get_session_scorecard(request, event)
    form = ScorecardForm(event=event) if event.state == "open" else None

    return render(
        request,
        "tasting/event_detail.html",
        {
            "event": event,
            "qr_svg": qr_svg,
            "existing_scorecard": existing_scorecard,
            "form": form,
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
    return render(
        request,
        "tasting/scorecard_detail.html",
        {"scorecard": scorecard},
    )


def _get_session_scorecard(request, event):
    """Look up an existing scorecard from the session."""
    scorecard_id = request.session.get(event.public_id)
    if not scorecard_id:
        return None
    return Scorecard.objects.filter(public_id=scorecard_id, event=event).first()
