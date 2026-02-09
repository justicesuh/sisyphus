FROM python:3.14-slim-bookworm

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin

ENV PYTHONUBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /usr/app

COPY pyproject.toml .
COPY uv.lock .
RUN uv sync --locked
RUN uv run playwright install --with-deps
COPY . .

EXPOSE 8000
CMD ["uv", "run", "gunicorn", "sisyphus.wsgi", "--bind", "0.0.0.0:8000"]
