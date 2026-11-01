# Stage 1: install dependencies with uv
FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim AS builder

WORKDIR /app

# Copy dependency files first, so the dependency layer is cached
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra prod --no-install-project

COPY src/ ./src/
COPY manage.py ./
RUN uv sync --frozen --no-dev --extra prod

# Stage 2: runtime
FROM python:3.14-slim-trixie

RUN groupadd -r django && useradd -r -g django django
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src
COPY --from=builder /app/manage.py ./
COPY entrypoint.sh ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=velunt.settings.prod

# The base settings suffice for collecting static files, and need no secrets
RUN DJANGO_SETTINGS_MODULE=velunt.settings.base python manage.py collectstatic --noinput

USER django
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]
