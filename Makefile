test:
	pytest -q

lint:
	ruff check . && ruff format --check .

up:
	docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d
