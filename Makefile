.PHONY: build
build:
	docker compose -p sisyphus --verbose build

.PHONY up:
up:
	docker compose -p sisyphus up -d

.PHONY: down
down:
	docker compose -p sisyphus down

.PHONY: shell
shell:
	docker exec -it sisyphus_python /bin/bash
