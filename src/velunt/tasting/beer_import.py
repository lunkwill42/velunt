"""Parsing of beer lists pasted from spreadsheets.

Copying cells from a spreadsheet yields one line per row, with cells separated by
tabs. The first row holds column titles, unless it already contains a URL. The
name column is the one titled like "Navn", otherwise the first column. A column
titled "Hjemmebrygg" marks homebrews, and any other column containing URLs holds
links whose label is the column title.
"""

from dataclasses import dataclass, field
from urllib.parse import urlsplit

NAME_TITLES = {"navn", "ølnavn", "øl", "name", "beer"}
HOMEBREW_TITLES = {"hjemmebrygg", "homebrew"}
FALSE_VALUES = {"", "0", "-", "false", "no", "nei", "n"}
KNOWN_LINK_LABELS = {
    "vinmonopolet.no": "Vinmonopolet",
    "untappd.com": "Untappd",
    "ratebeer.com": "RateBeer",
}


@dataclass
class ParsedLink:
    label: str
    url: str


@dataclass
class ParsedBeer:
    name: str
    is_homebrew: bool = False
    links: list[ParsedLink] = field(default_factory=list)


@dataclass
class ParsedBeerList:
    beers: list[ParsedBeer] = field(default_factory=list)
    ignored_columns: list[str] = field(default_factory=list)


@dataclass
class Columns:
    name: int
    homebrew: int | None
    links: dict[int, str]
    ignored: list[str]


def parse_beer_list(text):
    """Parse tab-separated spreadsheet rows into a list of unique beers"""
    rows = _split_rows(text)
    if not rows:
        return ParsedBeerList()
    titles, data_rows = _split_titles(rows)
    columns = _classify_columns(titles, data_rows)
    beers = [_parse_row(row, columns) for row in data_rows]
    return ParsedBeerList(
        beers=_merge_duplicates(beer for beer in beers if beer.name),
        ignored_columns=columns.ignored,
    )


def parse_bool(value):
    """Interpret a spreadsheet cell as a yes/no value"""
    return value.strip().casefold() not in FALSE_VALUES


def label_for_url(url):
    """Make a link label from a URL's domain name"""
    hostname = (urlsplit(url).hostname or "").removeprefix("www.")
    for domain, label in KNOWN_LINK_LABELS.items():
        if hostname == domain or hostname.endswith(f".{domain}"):
            return label
    return hostname or url


def _split_rows(text):
    rows = [[cell.strip() for cell in line.split("\t")] for line in text.splitlines()]
    rows = [row for row in rows if any(row)]
    width = max((len(row) for row in rows), default=0)
    return [row + [""] * (width - len(row)) for row in rows]


def _split_titles(rows):
    if any(_is_url(cell) for cell in rows[0]):
        return [""] * len(rows[0]), rows
    return rows[0], rows[1:]


def _classify_columns(titles, data_rows):
    normalized = [title.casefold() for title in titles]
    homebrew = _first_index(normalized, HOMEBREW_TITLES, default=None)
    name = _first_index(normalized, NAME_TITLES, default=1 if homebrew == 0 else 0)
    links = {}
    ignored = []
    for index, title in enumerate(titles):
        if index in (name, homebrew):
            continue
        if any(_is_url(row[index]) for row in data_rows):
            links[index] = title
        else:
            ignored.append(title or f"Kolonne {index + 1}")
    return Columns(name=name, homebrew=homebrew, links=links, ignored=ignored)


def _parse_row(row, columns):
    beer = ParsedBeer(name=row[columns.name])
    if columns.homebrew is not None:
        beer.is_homebrew = parse_bool(row[columns.homebrew])
    for index, title in columns.links.items():
        url = row[index]
        if _is_url(url):
            beer.links.append(ParsedLink(label=title or label_for_url(url), url=url))
    return beer


def _merge_duplicates(beers):
    """Merge beers listed more than once, such as control beers"""
    merged = {}
    for beer in beers:
        existing = merged.setdefault(beer.name.casefold(), beer)
        if existing is beer:
            continue
        existing.is_homebrew = existing.is_homebrew or beer.is_homebrew
        known_urls = {link.url for link in existing.links}
        existing.links += [link for link in beer.links if link.url not in known_urls]
    return list(merged.values())


def _first_index(values, wanted, default):
    return next((i for i, value in enumerate(values) if value in wanted), default)


def _is_url(value):
    return value.casefold().startswith(("http://", "https://"))
