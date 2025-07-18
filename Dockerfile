FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .

CMD /bin/bash
