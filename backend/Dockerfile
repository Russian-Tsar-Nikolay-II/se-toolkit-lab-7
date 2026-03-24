# Adapted from https://github.com/astral-sh/uv-docker-example/blob/fa761744819c05f4ce207bde1f0a396f6be3915f/multistage.>
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=backend/pyproject.toml,target=backend/pyproject.toml \
    --mount=type=bind,source=bot/pyproject.toml,target=bot/pyproject.toml \
    uv sync --locked --no-install-project

COPY backend /app/backend
COPY bot /app/bot
COPY pyproject.toml uv.lock /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX=harbor.pg.innopolis.university/docker-hub-cache/
FROM ${REGISTRY_PREFIX}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

COPY --from=builder --chown=nonroot:nonroot /app /app

ENV PATH="/app/.venv/bin:$PATH"

USER nonroot
WORKDIR /app

CMD ["sh", "-c", "python backend/app/run.py"]
