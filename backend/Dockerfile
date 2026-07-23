FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.25 /uv /usr/local/bin/uv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./backend/

RUN uv sync --frozen --no-dev

FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/ /app/

# WORKDIR creates /app as root; chown so the non-root user can create the
# runtime data dir (SQLite checkpoints) under it at startup.
RUN chown appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
