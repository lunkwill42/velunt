from django.shortcuts import get_object_or_404, render

from velunt.tasting.models import Event
from velunt.tasting.qr import generate_qr_svg


def event_detail(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    event_url = request.build_absolute_uri()
    qr_svg = generate_qr_svg(event_url)
    return render(
        request,
        "tasting/event_detail.html",
        {"event": event, "qr_svg": qr_svg},
    )
