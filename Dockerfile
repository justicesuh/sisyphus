FROM python:3.14-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin

WORKDIR /usr/app

CMD /bin/bash
