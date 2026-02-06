.PHONY: build
build:
	docker compose -p sisyphus --verbose build

.PHONY up:
up:
	docker compose -p sisyphus up -d

.PHONY: down
down:
	docker compose -p sisyphus down

.PHONY: lock
lock:
	docker exec -it sisyphus_django uv lock

.PHONY: sync
sync:
	docker exec -it sisyphus_django uv sync --locked

.PHONY: serve
serve:
	docker exec -it sisyphus_django uv run manage.py runserver 0.0.0.0:8000

.PHONY: check
check:
	docker exec -it sisyphus_django uv run manage.py check

.PHONY: typecheck
typecheck:
	docker exec -it sisyphus_django uv run mypy sisyphus

.PHONY: lint
lint:
	docker exec -it sisyphus_django uv run ruff check sisyphus

.PHONY: fix
fix:
	docker exec -it sisyphus_django uv run ruff check --fix sisyphus

.PHONY: format
format:
	docker exec -it sisyphus_django uv run ruff format sisyphus

.PHONY: migrations
migrations:
	docker exec -it sisyphus_django uv run manage.py makemigrations

.PHONY: migrate
migrate:
	docker exec -it sisyphus_django uv run manage.py migrate

.PHONY: shell
shell:
	docker exec -it sisyphus_django /bin/bash

.PHONY: logs
logs:
	docker compose logs -f
