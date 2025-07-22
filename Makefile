ifneq (,$(wildcard ./.env))
	include .env
	export
endif

NAME := sisyphus

PORT := 8000

.PHONY: build
build:
	docker compose -p ${NAME} --verbose build

.PHONY: up
up:
	docker compose -p ${NAME} up -d

.PHONY: down
down:
	docker compose -p ${NAME} down

.PHONY: serve
serve:
	docker exec -it ${NAME}_django python manage.py runserver 0.0.0.0:${PORT}

.PHONY: migrations
migrations:
	docker exec -it ${NAME}_django python manage.py makemigrations

.PHONY: migrate
migrate:
	docker exec -it ${NAME}_django python manage.py migrate

.PHONY: lint
lint:
	docker exec -it ${NAME}_django flake8 ${NAME}

.PHONY: shell
shell:
	docker exec -it ${NAME}_django /bin/bash

.PHONY: superuser
superuser:
	docker exec -it ${NAME}_django python manage.py shell -c "from sisyphus.users.models import User; User.objects.create_superuser('$(DJANGO_ADMIN_EMAIL)', '$(DJANGO_ADMIN_PASSWORD)')"

.PHONY: addrules
addrules:
	docker exec -it ${NAME}_django python manage.py addrules

.PHONY: processrules
processrules:
	docker exec -it ${NAME}_django python manage.py processrules

.PHONY: search
search:
	docker exec -it ${NAME}_django python manage.py search

.PHONY: populate
populate:
	docker exec -it ${NAME}_django python manage.py populate
