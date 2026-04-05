from collections import defaultdict
from decimal import Decimal

from velunt.tasting.models import ScorecardLine
from velunt.tasting.scoring import get_scoring_system


def compute_results(event):
    """Compute ranked results for a closed event with a published answer key.

    Returns a dict with `ranked_beers` and `scorecards`.
    """
    scoring_system = get_scoring_system(event.scoring_system)
    answer_key = _get_answer_key_map(event)
    duplicate_groups, duplicate_siblings = _find_duplicate_groups(event)
    total_judges = event.scorecards.count()

    all_lines = (
        ScorecardLine.objects.filter(scorecard__event=event)
        .select_related("scorecard")
        .order_by("scorecard__judge_name")
    )

    beer_scores = defaultdict(list)
    beer_judge_lines = defaultdict(list)
    for line in all_lines:
        beer_judge_lines[line.beer_number].append(line)
        if line.total_score is not None:
            beer_scores[line.beer_number].append(line.total_score)

    all_beer_numbers = set(beer_judge_lines.keys())
    if answer_key:
        all_beer_numbers |= set(answer_key.keys())

    all_scorecards = list(event.scorecards.all().order_by("judge_name"))

    ranked = []
    for beer_number in all_beer_numbers:
        totals = beer_scores.get(beer_number, [])
        avg_score = scoring_system.aggregate(totals) if totals else Decimal("0")
        entry = answer_key.get(beer_number)

        lines_by_scorecard = {
            line.scorecard_id: line for line in beer_judge_lines.get(beer_number, [])
        }
        judge_entries = [
            {
                "judge_name": sc.judge_name,
                "line": lines_by_scorecard.get(sc.id),
            }
            for sc in all_scorecards
        ]

        ranked.append(
            {
                "rank": 0,
                "beer_number": beer_number,
                "beer_name": entry.beer.name if entry else f"Ukjent øl #{beer_number}",
                "beer": entry.beer if entry else None,
                "avg_score": avg_score,
                "judge_count": len(totals),
                "total_judges": total_judges,
                "is_duplicate": beer_number in duplicate_groups,
                "duplicate_group_id": duplicate_groups.get(beer_number),
                "duplicate_siblings": duplicate_siblings.get(beer_number, []),
                "judge_entries": judge_entries,
            }
        )

    ranked.sort(key=lambda r: r["avg_score"], reverse=True)
    for i, entry in enumerate(ranked, 1):
        entry["rank"] = i

    scorecards = event.scorecards.prefetch_related("lines").all()

    return {
        "ranked_beers": ranked,
        "scorecards": scorecards,
        "scoring_system": scoring_system,
    }


def _get_answer_key_map(event):
    """Build a dict of beer_number → AnswerKeyEntry."""
    try:
        ak = event.answer_key
    except event.__class__.answer_key.RelatedObjectDoesNotExist:
        return {}
    if not ak.is_published:
        return {}
    entries = ak.entries.select_related("beer").all()
    return {e.beer_number: e for e in entries}


def _find_duplicate_groups(event):
    """Find beer numbers that share the same Beer (control beers).

    Returns a tuple of:
    - dict of beer_number → group_id (integer)
    - dict of beer_number → list of sibling beer numbers (excluding self)
    """
    try:
        ak = event.answer_key
    except event.__class__.answer_key.RelatedObjectDoesNotExist:
        return {}, {}
    entries = ak.entries.all()
    beer_to_numbers = defaultdict(list)
    for entry in entries:
        beer_to_numbers[entry.beer_id].append(entry.beer_number)

    group_map = {}
    siblings_map = {}
    group_id = 0
    for numbers in beer_to_numbers.values():
        if len(numbers) > 1:
            for n in numbers:
                group_map[n] = group_id
                siblings_map[n] = [s for s in numbers if s != n]
            group_id += 1
    return group_map, siblings_map
