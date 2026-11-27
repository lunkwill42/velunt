"""Editing of an event's answer key, with one row per beer number.

The rows are the numbers the judges have scored, plus any numbers already in the
answer key. A row left empty gets no answer key entry. That is how numbers a judge
made up by mistake are left out.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from django.db import transaction

from velunt.tasting.models import AnswerKey, AnswerKeyEntry, Beer, ScorecardLine


@dataclass
class AnswerKeyRow:
    beer_number: int
    # What was typed or saved; `beer` is set only when it is on the beer list
    beer_name: str = ""
    beer: Beer | None = None
    judge_names: list[str] = field(default_factory=list)
    total_judges: int = 0
    # Other numbers given the same beer, as when a beer is served twice on purpose
    sibling_numbers: list[int] = field(default_factory=list)
    error: str = ""

    @property
    def field_name(self):
        return f"beer_{self.beer_number}"

    @property
    def is_on_few_scorecards(self):
        """Whether fewer than half the judges scored it, which hints at a typo"""
        return 2 * len(self.judge_names) < self.total_judges

    @property
    def is_on_all_scorecards(self):
        return len(self.judge_names) >= self.total_judges

    @property
    def has_notes(self):
        return bool(
            self.error
            or not self.judge_names
            or not self.is_on_all_scorecards
            or self.sibling_numbers
        )


@dataclass
class AnswerKeyEdit:
    rows: list[AnswerKeyRow]

    @property
    def has_errors(self):
        return any(row.error for row in self.rows)

    @property
    def first_error_number(self):
        """The beer number to focus after a rejected save"""
        return next((row.beer_number for row in self.rows if row.error), None)


def get_answer_key_edit(event, data=None):
    """Build the rows from the saved answer key, or from posted `data`"""
    rows = _make_rows(event)
    if data is None:
        _fill_in_saved_beers(event, rows)
    else:
        _fill_in_posted_beers(event, rows, data)
    _find_siblings(rows)
    return AnswerKeyEdit(rows=rows)


def save_answer_key(event, edit):
    """Replace the answer key entries with the beers named in a valid `edit`

    The rows come from the database when the form is posted, not when it was shown.
    A number that has since left every scorecard is ignored, and the last save wins.
    """
    with transaction.atomic():
        answer_key, _ = AnswerKey.objects.get_or_create(
            event=event,
            # The host is not logged in, and acts on behalf of the event owner
            defaults={"created_by": event.owner},
        )
        answer_key.entries.all().delete()
        AnswerKeyEntry.objects.bulk_create(
            AnswerKeyEntry(
                answer_key=answer_key,
                beer_number=row.beer_number,
                beer=row.beer,
            )
            for row in edit.rows
            if row.beer
        )


def get_unnumbered_beers(event):
    """Beers on the event's list that the saved answer key does not use"""
    return event.beers.filter(answer_key_entries__isnull=True)


def _make_rows(event):
    judges_by_number = defaultdict(list)
    lines = ScorecardLine.objects.filter(scorecard__event=event).order_by(
        "scorecard__judge_name"
    )
    for beer_number, judge_name in lines.values_list(
        "beer_number", "scorecard__judge_name"
    ):
        judges_by_number[beer_number].append(judge_name)
    numbers = set(judges_by_number) | set(
        AnswerKeyEntry.objects.filter(answer_key__event=event).values_list(
            "beer_number", flat=True
        )
    )
    # Judges who scored nothing, as after registering twice, would skew the share
    total_judges = len({name for names in judges_by_number.values() for name in names})
    return [
        AnswerKeyRow(
            beer_number=number,
            judge_names=judges_by_number[number],
            total_judges=total_judges,
        )
        for number in sorted(numbers)
    ]


def _fill_in_saved_beers(event, rows):
    entries = AnswerKeyEntry.objects.filter(answer_key__event=event)
    beers = {entry.beer_number: entry.beer for entry in entries.select_related("beer")}
    for row in rows:
        row.beer = beers.get(row.beer_number)
        row.beer_name = row.beer.name if row.beer else ""


def _fill_in_posted_beers(event, rows, data):
    beers = _get_beers_by_name(event)
    for row in rows:
        row.beer_name = data.get(row.field_name, "").strip()
        if not row.beer_name:
            continue
        beer = beers.get(row.beer_name.casefold())
        if beer is None:
            row.error = f"Fant ikke «{row.beer_name}» på øllisten."
            continue
        row.beer = beer
        # Use the spelling from the beer list, whatever case was typed
        row.beer_name = beer.name


def _find_siblings(rows):
    numbers_by_beer = defaultdict(list)
    for row in rows:
        if row.beer:
            numbers_by_beer[row.beer].append(row.beer_number)
    for row in rows:
        numbers = numbers_by_beer.get(row.beer, [])
        row.sibling_numbers = [n for n in numbers if n != row.beer_number]


def _get_beers_by_name(event):
    return {beer.name.casefold(): beer for beer in event.beers.all()}
