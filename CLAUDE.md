# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Velunt is a web-based beer tasting event management system. Participants at blind tasting events scan a QR code to access a judging form on their phone, score each beer, and the system produces ranked results and statistics. No user registration required for judges — only event organizers need Django accounts.

## Tech Stack

- **Backend:** Python 3.14, Django 5.2 LTS
- **Frontend:** Django templates + HTMX + Pico CSS (mobile-first, static assets vendored)
- **Database:** PostgreSQL
- **Key libraries:** django-htmx, pytest-django, python-qrcode
- **Code standards:** Follow conventions from [Uninett/nav](https://github.com/Uninett/nav)

## Project Structure

All Python source code lives under `src/`. The project uses the `velunt` namespace:

- `src/velunt/settings.py`, `src/velunt/urls.py` — Django project configuration.
- `src/velunt/accounts/` — Custom User model (`AbstractUser` subclass). `AUTH_USER_MODEL = "accounts.User"`.
- `src/velunt/tasting/` — The main Django app for tasting event logic.
- `tests/` — Test suite (top-level, not inside `src/`).

## Key Domain Concepts

- **Arrangement (Event):** A tasting event with a non-guessable short ID, created by an authenticated Django user. Can be open (accepting submissions) or closed.
- **Dommerskjema (Scorecard):** A judge's scoring form, also with a non-guessable short ID. Judges identified by name only (unique per event). No login required — access controlled via secret URLs and browser cookies/local storage.
- **Fasit (Answer key):** Maps beer numbers to actual beer names/URLs. Entered after tasting, possibly uploaded via spreadsheet.
- **Poengsystem (Scoring system):** Configurable per event. Each system has 1+ dimensions with min/max, increment rules, and a formula for total score.

## Scoring Systems (built-in)

1. **Juleøl (Christmas beer):** Two dimensions — "Untappd" (1.0–5.0, 0.25 increments) and "Julete" (1.0–5.0, 0.25 increments). Total = Untappd × Julete.
2. **Simple Untappd:** One dimension — Untappd scale (0.0–5.0, 0.1 increments). Total = sum.

## Language & Locale

- All UI text must be in Norwegian (bokmål). Code, models, and attributes use English names.
- Timezone: Norway (Europe/Oslo).
- Prepare for i18n so English translations can be added later.

## ID Design

Event and scorecard IDs must be short enough for humans to type, but not guessable sequential numbers. The system will likely never exceed 100 events, so balance brevity against collision resistance.

## Toolchain

- Use **uv** for dependency management and virtual environments.

## Code Style

- **Ruff** for both formatting and linting (config in `pyproject.toml`).
- Max line width: 88. Long test names are acceptable — add `# noqa: E501` instead of shortening them.
- Format quote style: `"preserve"`.
- Follow Robert Martin's **step-down rule**: higher-level functions appear before the lower-level functions they call. Since Python requires definitions before use in some contexts, this cannot always be followed strictly, but aim for it where possible.

## Commits

- The subject line completes the sentence: *"If applied, this commit will ..."*
- Start with a capital letter, do not end with punctuation.
- Keep the subject line to 50 characters or less.
- Separate subject from body with a blank line; wrap body at 72 characters.
- Use the body to explain *what* and *why*, not *how*.
- Restrained use of markdown in commit messages is fine; use backticks to quote function names and code identifiers.
- NEVER add `Co-Authored-By` or other AI attribution tags to commit messages.
- Prefer small, focused commits that touch a single concept. Each commit should make sense on its own and produce a useful `git blame` history. Avoid lumping unrelated changes together.

## Testing

- Use `pytest` as the test runner.
- Tests live in a top-level `tests/` directory.
- **Test naming**: `test_when_<condition>_<subject>_should_<assertion>`
  - `<condition>` — the given/when precondition.
  - `<subject>` — what is being tested; use `it` if the test class already names the function under test.
  - `<assertion>` — expected outcome.
  - Example: `test_when_queue_is_empty_it_should_return_false`
