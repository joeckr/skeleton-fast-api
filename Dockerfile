FROM ghcr.io/astral-sh/uv:0.13-python3.14-alpine AS builder

WORKDIR /app

COPY src/pyproject.toml src/uv.lock ./

RUN uv sync --frozen --no-dev

COPY src/. .

FROM ghcr.io/joeckr/python:0.3.0

WORKDIR /app

COPY --from=builder /app /app
ENV PATH=/app/.venv/bin:$PATH
