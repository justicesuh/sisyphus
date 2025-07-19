FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/app

RUN apt update && apt install -y firefox-esr wget
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz
RUN tar -xvzf geckodriver-v0.36.0-linux64.tar.gz
RUN chmod +x geckodriver && mv geckodriver /usr/local/bin/geckodriver
RUN rm geckodriver-v0.36.0-linux64.tar.gz

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .

CMD /bin/bash
