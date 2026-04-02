# Velunt — MVP Specification

Velunt is a web-based system for conducting beer tasting events (typically blind
tastings). Judges scan a QR code to access a scorecard on their phone, score
each beer according to a configurable scoring system, and after the event is
closed the system presents ranked results and full scorecards.

## Tech Stack

- **Backend:** Python 3.14, Django 5.2 LTS (supported until April 2028)
- **Frontend:** Django templates + HTMX + Pico CSS (mobile-first). Static assets vendored, no CDN.
- **Database:** PostgreSQL
- **Deployment:** Docker Compose on a VPS
- **Email:** SMTP (existing server). Console backend in development.
- **QR codes:** python-qrcode (server-side generation)
- **Key libraries:** django-htmx (CSRF + request detection), pytest-django (testing)
- **Migrations:** Django's built-in migration system

## Data Model

All Python source code lives under `src/`. Tasting models live in `velunt.tasting`.
A separate `velunt.accounts` app holds the custom User model. The Django project
configuration lives under the `velunt` namespace (e.g. `velunt.settings`, `velunt.urls`).

### User (velunt.accounts)

A custom user model extending `AbstractUser`, initially with no extra fields.
Defined up front so the model can be extended later without migration pain.

```python
AUTH_USER_MODEL = "accounts.User"
```

### Event

| Field          | Type              | Notes                                                                                             |
|----------------|-------------------|---------------------------------------------------------------------------------------------------|
| id             | AutoField (PK)    | Internal, never exposed                                                                           |
| public_id      | CharField(unique) | 6 random alphanumeric chars (a-z, A-Z, 0-9)                                             |
| owner          | FK → User         | The Django user who created the event                                                             |
| description    | TextField         | Human-readable, e.g. "Juleølsmaking hos Vegard 2026"                                              |
| created_at     | DateTimeField     | Auto-set on creation                                                                              |
| event_date     | DateField         | Expected date of the tasting                                                                      |
| closed_at      | DateTimeField     | Null = not yet closed. Set when the organizer closes the event.                                   |
| scoring_system | CharField         | Key identifying the scoring system, e.g. `"juleol"`, `"simple_untappd"`. Choices defined in code. |

- `public_id` is used in all URLs. The internal `id` is never exposed to users.
- Organizers manage events via Django admin. The admin detail page should include a permalink to the public event page.

#### Event states

An event has three states, derived from `event_date` and `closed_at`:

1. **Not yet open** — current date is before `event_date` (midnight Europe/Oslo). The event page is visible but scorecard creation is not allowed.
2. **Open** — current date is on or after `event_date` and `closed_at` is null. Judges can create and edit scorecards.
3. **Closed** — `closed_at` is set. Scorecards are read-only, results are visible.

An organizer can **re-open** a closed event by clearing `closed_at` (setting it back to null via admin). This handles the "closed too early" case.

### Scorecard

| Field      | Type              | Notes                                   |
|------------|-------------------|-----------------------------------------|
| id         | AutoField (PK)    | Internal                                |
| public_id  | CharField(unique) | 6 random alphanumeric chars                 |
| event      | FK → Event        |                                         |
| judge_name | CharField         | Free-text, unique together with `event` |
| created_at | DateTimeField     | Auto-set                                |

- Anonymous users — no Django account required.
- The scorecard's `public_id` URL is the judge's "secret link" to their card.

### ScorecardLine

| Field       | Type           | Notes                                                                                                  |
|-------------|----------------|--------------------------------------------------------------------------------------------------------|
| id          | AutoField      |                                                                                                        |
| scorecard   | FK → Scorecard |                                                                                                        |
| beer_number | PositiveInt    | Unique together with `scorecard`                                                                       |
| scores      | JSONField      | Dict of dimension name → score value (e.g. `{"untappd": 3.5, "julete": 4.0}`)                          |
| total_score | DecimalField   | Computed and stored on save, using the event's scoring system formula. Null if the line is incomplete. |
| comment     | TextField      | Free-text tasting notes, optional                                                                      |
| created_at  | DateTimeField  |                                                                                                        |
| updated_at  | DateTimeField  | Auto-updated on save                                                                                   |

- `total_score` is calculated at save time using the scoring system's formula, making results immune to future changes in scoring system definitions.
- Rankings are computed from `AVG(total_score)` grouped by beer number — no need to re-evaluate the formula at display time.
- A null `total_score` indicates an incomplete line (excluded from rankings).

### AnswerKey (fasit)

| Field        | Type             | Notes                                                                                   |
|--------------|------------------|-----------------------------------------------------------------------------------------|
| id           | AutoField        |                                                                                         |
| event        | OneToOne → Event |                                                                                         |
| created_by   | FK → User        | The Django user who entered the answer key                                              |
| created_at   | DateTimeField    |                                                                                         |
| published_at | DateTimeField    | Null = draft. When set, the answer key becomes visible after this timestamp has passed. |

- The answer key can be created and edited at any time (before, during, or after the tasting).
- The answer key is **only visible to judges** when all conditions are met:
  1. The event is closed (`is_open = False`).
  2. `published_at` is not null.
  3. The current time is past `published_at`.
- Setting `published_at` to "now" publishes immediately. Setting it to a future time allows scheduling (e.g. "reveal at 22:00").
- This allows incremental entry (draft mode) without exposing partial or pre-tasting data.

### AnswerKeyEntry

| Field       | Type           | Notes                                          |
|-------------|----------------|------------------------------------------------|
| id          | AutoField      |                                                |
| answer_key  | FK → AnswerKey |                                                |
| beer_number | PositiveInt    | Unique together with `answer_key`              |
| name        | CharField      | Beer name (often brewery + beer name)          |
| url         | URLField       | Optional — link to Vinmonopolet, Untappd, etc. |

- MVP: one URL per entry. Post-MVP: multiple URLs with labels.
- Answer key is entered manually via Django admin (one beer at a time).

## ID Scheme

- Random alphanumeric string, **6 characters**.
- Alphanumeric only (a-z, A-Z, 0-9) — no special characters.
- Generated using `secrets.choice()` from the standard library (no external dependency).
- Checked for uniqueness on creation.
- At the expected scale (<100 events, <1000 scorecards), collision risk is negligible.

## Authentication & Sessions

### Judges (anonymous)
- No login required. Django's session framework tracks anonymous users.
- Session age: 90 days (`SESSION_COOKIE_AGE`).
- When a judge creates a scorecard, the scorecard's `public_id` is stored in `request.session` keyed by the event's `public_id`.
- On returning to the event page, the server checks the session for an existing scorecard and renders a link to it.
- Judges can also bookmark their scorecard URL directly (the scorecard page provides a "copy link" feature as a fallback for session loss).

### Organizers
- Standard Django user accounts, managed via `createsuperuser` or admin.
- Password reset via email must be supported.
- All event management (create, close, fasit entry) happens in Django admin.
- Organizers can only see/edit their own events (superusers can see all).

## User Flows

### Judge Flow
1. Scan QR code (or receive URL) → **Event page**
2. Event page shows: event description, date, open/closed status, and a prominent QR code linking to itself (so the organizer can open the page on their device and show it for others to scan).
3. If event is not yet open (before `event_date`) → show event info but no scorecard form.
4. If session contains a scorecard for this event → show "Continue your scorecard" link.
5. Otherwise → show "Create scorecard" form (enter judge name). If the name is already taken, show an error asking the judge to add a distinguishing detail (e.g. "Morten B" or "Morten (Bergen)").
5. On scorecard page: enter beer number, fill in score dimensions, optional comment. Form suggests next sequential number but allows skipping/changing.
6. Each score line auto-saves via HTMX as it's entered or changed.
7. Scores are freely editable as long as the event is open.
8. When event is closed → scorecard becomes read-only.
9. Event page now shows results (ranked list, all scorecards).

### Organizer Flow
1. Log in to Django admin.
2. Create event: fill in description, date, select scoring system.
3. System generates `public_id` automatically.
4. Generate QR code for the event (admin action or link in admin).
5. Print/share QR code at the tasting event.
6. After tasting: close event (set `is_open = False`).
7. Enter fasit via admin (add AnswerKeyEntry records).
8. Results are now visible on the event page.

## Scoring Systems

Scoring systems are defined in code (not user-configurable in MVP). Each system specifies:
- A set of **dimensions**, each with: name, label (Norwegian), min, max, increment, whether integers only.
- A **total score formula** combining the dimensions into a per-line total.
- An **aggregation method** for ranking beers across judges (e.g. average, median). Both built-in systems use average for MVP, but the structure allows other methods in the future.

### Recalculation

The Django admin should provide an action to **recalculate all total scores** for an event. This re-applies the scoring system's formula to every line in the event, overwriting stored `total_score` values. Useful if scores were imported incorrectly or a bug is discovered.

### Built-in systems

#### Juleøl (Christmas beer)
| Dimension | Label    | Min | Max | Increment | Type  |
|-----------|----------|-----|-----|-----------|-------|
| untappd   | Untappd  | 1.0 | 5.0 | 0.25      | Float |
| julete    | Julete   | 1.0 | 5.0 | 0.25      | Float |

**Total score** = untappd × julete (range: 1.0–25.0)

#### Simple Untappd
| Dimension | Label   | Min | Max | Increment | Type  |
|-----------|---------|-----|-----|-----------|-------|
| untappd   | Untappd | 0.0 | 5.0 | 0.1       | Float |

**Total score** = untappd (range: 0.0–5.0)

## Scorecard UX

- **Mobile-first** design — the primary interface is a phone screen.
- Beer numbers are entered sequentially (form suggests the next number) but judges can skip or go back to any number.
- **Auto-save:** score lines are saved to the server via HTMX as fields are changed. Partial lines (e.g. beer number entered but not all scores filled) are saved but flagged as incomplete. Incomplete lines are excluded from results calculations, and the UI should visually indicate to the judge that the line is incomplete.
- **Editable:** judges can change any score as long as the event is open.
- **Comments:** free-text field per beer for tasting notes.
- Score inputs should enforce the scoring system's constraints (min/max, valid increments).
- The scorecard page should display its own URL (or offer a "copy link" button) so judges can bookmark it or recover access if their session is lost.

## Results & Scorecard Visibility

### During an open event
- A judge can only see their **own** scorecard. No access to other judges' scores.
- The event page shows event info and the judge's own scorecard link (if they have one).

### After the event is closed
- The event page shows:
  - If the answer key is **not yet published**: show a "results pending" message. No scores or rankings are shown.
  - If the answer key **is published**:
    - **Ranked beer list**: beers sorted by average total score across judges who scored them. Beers that were not scored by all judges should be highlighted (e.g. "scored by 7 of 9 judges").
    - **Fasit info**: real beer name and URL for each beer number.
    - **All scorecards**: every judge's full scorecard (scores + tasting notes) is visible.
- No authentication required to view results — anyone with the event URL can see them.

## Edge Cases

- **Orphaned beer numbers**: Judges may score beer numbers that don't exist in the answer key (e.g. scoring beer #15 when the answer key only lists 1–12). The results page should handle this gracefully — show the score but without a beer identity.
- **Scorecard deletion**: Judges cannot delete their own scorecards. If a scorecard was created by mistake (wrong name, duplicate person), the organizer can delete it via Django admin.
- **Concurrent edits**: If a judge has their scorecard open in multiple tabs, auto-saves from both may overwrite each other. Acceptable for MVP — last write wins.

## QR Code

- Generated server-side using `python-qrcode`.
- The QR code encodes the full URL to the event page.
- Displayed prominently on the event page itself, so the organizer can simply open the page and show their screen for judges to scan.
- Also available as a downloadable/printable image from Django admin.

## Locale & Language

- All UI text in Norwegian (bokmål).
- Model names, field names, and code in English.
- Timezone: `Europe/Oslo`.
- Use Django's i18n framework so English translations can be added later.

## Deployment

- **Production:** Docker Compose with at least: Django app container, PostgreSQL container. Static files served via whitenoise or nginx. The VPS already runs other sites and a PostgreSQL server.
- **Development:** A `docker-compose.dev.yml` (or similar) that starts a PostgreSQL container for local development. The Django dev server runs on the host (not in a container), connecting to the containerized database.

## Development Standards

### Project metadata

- Use `pyproject.toml` for all project configuration (no `setup.py` or `setup.cfg`).
- License: MIT.

### Toolchain

- Use **uv** for dependency management and virtual environments.

### Code formatting and linting

- **Ruff** for both formatting and linting.
- Max line width: 88. Long test names are acceptable — add `# noqa: E501` instead of shortening them.
- Import sorting via Ruff's isort rules.
- Ruff lint rules: at minimum `["BLE001", "E4", "E501", "E7", "E9", "F", "I"]` (the `I` enables import sorting).
- Format quote style: `"preserve"`.

### Code organization

- Follow Robert Martin's **step-down rule**: higher-level functions appear before the lower-level functions they call. Since Python requires definitions before use in some contexts, this cannot always be followed strictly, but aim for it where possible.

### Pre-commit hooks

Use `pre-commit` with the following hooks (matching NAV's setup):

- `pre-commit-hooks`: trailing-whitespace, mixed-line-ending, end-of-file-fixer.
- `ruff-pre-commit`: ruff-format (formatting) and ruff (linting).

### Commit messages

Follow the conventions from NAV's contributor checklist (based on https://cbea.ms/git-commit/):

- The first line completes the sentence: *"If applied, this commit will ..."*
- Start with a capital letter.
- Do not end with punctuation.
- Keep the first line to 50 characters or less.
- Separate subject from body with a blank line.
- Wrap the body at 72 characters.
- Use the body to explain *what* and *why*, not *how*.
- Restrained use of markdown in commit messages is fine; use backticks to quote function names and code identifiers.
- NEVER add `Co-Authored-By` or other AI attribution tags to commit messages.

### Testing

- Use `pytest` as the test runner.
- Tests live in a top-level `tests/` directory.
- **Test naming**: use the pattern `test_when_<condition>_<subject>_should_<assertion>`:
  - `<condition>` — the given/when precondition.
  - `<subject>` — what is being tested; use `it` if the test class already names the function under test, otherwise use the function name.
  - `<assertion>` — expected outcome.
  - Example: `test_when_queue_is_empty_it_should_return_false`

---

## Prioritized Feature List

### MVP (Priority 1 — implement in this order)

1. **Project scaffolding** — Django project, settings, Docker Compose, PostgreSQL config.
2. **Scoring system definitions** — Define the two built-in systems in code.
3. **Event model + admin** — Create/edit events in Django admin, auto-generate `public_id`.
4. **Event page** — Public page showing event info, open/closed status.
5. **Scorecard creation** — Judge enters name on event page, scorecard created, stored in session.
6. **Scorecard page + score entry** — Enter beer numbers and scores, auto-save via HTMX, input validation.
7. **Scorecard editing** — Modify existing scores while event is open, read-only when closed.
8. **Fasit model + admin** — Enter answer key via Django admin.
9. **Results page** — Ranked beer list, fasit info, all scorecards visible (only when event is closed).
10. **QR code generation** — Server-side QR image for event URL, accessible from admin.
11. **Password reset** — Email-based password reset for organizer accounts.
12. **Norwegian UI text** — All user-facing text in Norwegian with i18n markup.
13. **Mobile styling** — Responsive, mobile-first CSS.

### Post-MVP (Priority 2)

- Fasit upload via CSV or Excel spreadsheet.
- Multiple URLs per fasit entry (with labels: Vinmonopolet, Untappd, Brewfather, etc.).
- Judge statistics: most/least generous scorer, average scores.
- Control beer variance analysis (same beer served twice under different numbers).
- Custom organizer pages (outside Django admin) for managing events and fasit.
- Secret URL for fasit entry (so a non-admin can enter it).
- Email/copy scorecard URL to judge.
- English translation.
