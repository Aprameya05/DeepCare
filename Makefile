COMPOSE = docker compose -f clinicaliq/docker-compose.yml

.PHONY: setup up down migrate seed test logs clean

setup:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

migrate:
	$(COMPOSE) exec -T backend alembic -c backend/alembic.ini upgrade head

seed:
	$(COMPOSE) exec -T backend python -m backend.scripts.seed_disease_test_rules
	$(COMPOSE) exec -T backend python -m backend.scripts.seed_country_pricing

test:
	$(COMPOSE) exec -T backend pytest --cov=backend --cov-report=term-missing
	cd clinicaliq/frontend && npm run test:e2e

logs:
	$(COMPOSE) logs -f

clean:
	$(COMPOSE) down -v --remove-orphans
