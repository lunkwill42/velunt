# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Velunt is a web-based beer tasting event management system. Participants at blind tasting events scan a QR code to access a judging form on their phone, score each beer, and the system produces ranked results and statistics. No user registration is required for judges: only event organizers need Django accounts.

## Tech Stack

- **Backend:** Python 3.14, Django 5.2 LTS
- **Frontend:** Django templates + HTMX + Pico CSS (mobile-first, static assets vendored)
- **Database:** PostgreSQL
- **Key libraries:** django-htmx, pytest-django, python-qrcode
- **Code standards:** Follow conventions from [Uninett/nav](https://github.com/Uninett/nav)

## Project Structure

All Python source code lives under `src/`. The project uses the `velunt` namespace:

- `src/velunt/settings/` - Django settings. `base.py` holds what all environments share, while `dev.py` and `prod.py` add what is unique to development and production. `manage.py` defaults to `dev`, the WSGI/ASGI entry points to `prod`.
- `src/velunt/urls.py` - Root URL configuration.
- `src/velunt/accounts/` - Custom User model (`AbstractUser` subclass). `AUTH_USER_MODEL = "accounts.User"`.
- `src/velunt/tasting/` - The main Django app for tasting event logic.
- `tests/` - Test suite (top-level, not inside `src/`).

## Settings

- Never gate settings or behaviour on `DEBUG` (no `if not DEBUG:` in `base.py` or elsewhere). Put what differs between environments in `dev.py` or `prod.py` instead.
- The reason is troubleshooting: turning `DEBUG` on in production must not change anything else about how production behaves.
- Production reads secrets from environment variables and refuses to start without them (`get_str_env(..., required=True)`).

## Branches and Deployment

- `main` is what runs in production. Never commit directly to `main`; do all work on a feature branch.
- The deployment configuration lives outside this repository. When a change needs new environment variables or services, say so explicitly in the pull request description.

## Key Domain Concepts

- **Arrangement (Event):** A tasting event with a non-guessable short ID, created by an authenticated Django user. Can be open (accepting submissions) or closed.
- **Dommerskjema (Scorecard):** A judge's scoring form, also with a non-guessable short ID. Judges identified by name only (unique per event). No login required; access is controlled via secret URLs and browser cookies/local storage.
- **Fasit (Answer key):** Maps beer numbers to actual beer names/URLs. Entered after tasting, possibly uploaded via spreadsheet.
- **Poengsystem (Scoring system):** Configurable per event. Each system has 1+ dimensions with min/max, increment rules, and a formula for total score.

## Scoring Systems (built-in)

1. **Juleøl (Christmas beer):** Two dimensions: "Untappd" (1.0–5.0, 0.25 increments) and "Julete" (1.0–5.0, 0.25 increments). Total = Untappd × Julete.
2. **Simple Untappd:** One dimension: Untappd scale (0.0–5.0, 0.1 increments). Total = sum.

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
- Max line width: 88. Long test names are acceptable: add `# noqa: E501` instead of shortening them.
- Format quote style: `"preserve"`.
- Follow Robert Martin's **step-down rule**: higher-level functions appear before the lower-level functions they call. Since Python requires definitions before use in some contexts, this cannot always be followed strictly, but aim for it where possible.
  - **This applies to test modules too.** Test functions and classes are the high-level readers, so they belong *above* the pytest fixtures and module-level helpers they use. Fixtures and helpers resolve at call time, so parking them at the top of a test file inverts step-down order.
- **Keep nesting shallow.** Deeply nested code is hard to read and reason about. Two remedies:
  1. **Return early.** Handle edge cases and failures first with guard clauses (`return`, `raise`, or `continue` in loops). The main path then stays at the outermost level instead of inside an `else`.
  2. **Extract nested logic into smaller functions.** When a nested block seems to need an explanatory comment, move it into a function whose name makes the comment unnecessary.
- Once a code pattern is repeated three times or more, refactor it to remove the redundancy, or at least point out the opportunity.

## Commits

- The subject line completes the sentence: *"If applied, this commit will ..."*
- Start with a capital letter, do not end with punctuation.
- Keep the subject line to 50 characters or less.
- Separate subject from body with a blank line; wrap body at 72 characters.
- Most commits need no body. Add one only when the *why* is not evident from the subject and the diff together.
- The body says why the change was made, to what end. It does not restate what the diff shows.
- Treat a body longer than the diff it describes as a smell, and cut it back unless the change is genuinely counter-intuitive.
- Each piece of rationale gets one home, not two:
  - Why a line or function is shaped the way it is goes in a code comment or docstring.
  - Why a set of changes hangs together goes in the commit body.
  - Why this approach rather than another goes in the pull request description or review discussion.
- One idea per sentence. Split a sentence that runs past roughly 25 words, or that needs more than one comma to hold together. This applies to code comments and docstrings as well.
- Restrained use of markdown in commit messages is fine; use backticks to quote function names and code identifiers.
- NEVER add `Co-Authored-By` or other AI attribution tags to commit messages.
- Prefer small, focused commits that touch a single concept. Each commit should make sense on its own and produce a useful `git blame` history. Avoid lumping unrelated changes together.

## Testing

- Use `pytest` as the test runner.
- Tests live in a top-level `tests/` directory, with subdirectories mirroring the package structure (e.g. `tests/tasting/` for `velunt.tasting`).
- **Test naming**: `test_when_<condition>_<subject>_should_<assertion>`
  - `<condition>`: the given/when precondition.
  - `<subject>`: what is being tested; use `it` if the test class already names the function under test.
  - `<assertion>`: expected outcome.
  - Example: `test_when_queue_is_empty_it_should_return_false`
