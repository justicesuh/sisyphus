FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/app

COPY pyproject.toml poetry.* .
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
COPY . .

CMD /bin/bash
