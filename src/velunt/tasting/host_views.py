"""Views for event hosts, who manage the beer list through a secret link"""

from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from velunt.tasting.beer_import import import_beer_list, parse_beer_list
from velunt.tasting.models import Beer, Event


def host_beer_list(request, token):
    event = _get_event(token)
    return render(
        request,
        "tasting/host_beer_list.html",
        {"event": event, "beers": _get_beers(event)},
    )


def preview_beer_import(request, token):
    """Show how pasted spreadsheet rows will be interpreted, without saving"""
    _get_event(token)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    text = request.POST.get("beer_list", "")
    return render(
        request,
        "tasting/_beer_import_preview.html",
        {"parsed": parse_beer_list(text), "has_input": bool(text.strip())},
    )


def import_beers(request, token):
    event = _get_event(token)
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    parsed = parse_beer_list(request.POST.get("beer_list", ""))
    result = import_beer_list(event, parsed, replace=bool(request.POST.get("replace")))
    messages.success(request, _describe_import(result))
    return redirect("tasting:host_beer_list", token=token)


def delete_beer(request, token, beer_id):
    event = _get_event(token)
    if request.method != "DELETE":
        return HttpResponseNotAllowed(["DELETE"])
    beer = get_object_or_404(Beer, pk=beer_id, event=event)
    error = None
    if beer.is_in_answer_key:
        error = f"{beer.name} er med i fasiten og kan ikke fjernes."
    else:
        beer.delete()
    return render(
        request,
        "tasting/_host_beer_list.html",
        {"event": event, "beers": _get_beers(event), "error": error},
    )


def _get_event(token):
    return get_object_or_404(Event, host_token=token)


def _get_beers(event):
    return event.beers.prefetch_related("links")


def _describe_import(result):
    parts = [f"La til {result.created} øl", f"oppdaterte {result.existing}"]
    if result.removed:
        parts.append(f"fjernet {result.removed}")
    description = ", ".join(parts) + "."
    if result.kept:
        description += (
            f" Beholdt {', '.join(result.kept)}, fordi de allerede er med i fasiten."
        )
    return description
