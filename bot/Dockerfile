FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
COPY backend/pyproject.toml backend/pyproject.toml
COPY bot ./bot

RUN uv sync --frozen --no-dev --package lms-bot

CMD ["uv", "run", "--frozen", "--package", "lms-bot", "python", "bot/bot.py"]
