# --- Stage-1: Builder
FROM python:3.14-slim AS builder

WORKDIR /app

# Pull uv from its official image — faster than installing via pip
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files only (layer cache: rebuild only when these change)
COPY pyproject.toml uv.lock ./

# Install deps into .venv, skip project install and dev deps
RUN uv sync --frozen --no-install-project --no-dev


# --- Stage-2: Runtime
FROM python:3.14-slim

WORKDIR /app

# Copy the venv
COPY --from=builder /app/.venv /app/.venv

COPY . .

# Pre-download HuggingFace model at build time so first request isn't slow
RUN /app/.venv/bin/python -c "\
from transformers import pipeline; \
pipeline('sentiment-analysis', model='cardiffnlp/twitter-roberta-base-sentiment-latest')"

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]