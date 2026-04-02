from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from velunt.tasting.models import Event


def event_detail(request, public_id):
    event = get_object_or_404(Event, public_id=public_id)
    return HttpResponse(f"Event: {event.description}")
