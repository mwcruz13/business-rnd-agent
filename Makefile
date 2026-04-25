BACKEND_SERVICE := bmi-backend
FRONTEND_SERVICE := bmi-frontend

.PHONY: up down logs test test-smoke cli migrate

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose up -d bmi-postgres $(BACKEND_SERVICE)
	docker compose exec -T $(BACKEND_SERVICE) alembic -c backend/migrations/alembic.ini upgrade head
	docker compose exec -T bmi-postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='bmi_test'" | grep -q 1 || \
		docker compose exec -T bmi-postgres psql -U postgres -c "CREATE DATABASE bmi_test"
	docker compose exec -T bmi-postgres psql -U postgres -d bmi_test -c "CREATE EXTENSION IF NOT EXISTS vector" 2>/dev/null || true
	docker compose exec -T $(BACKEND_SERVICE) pytest

test-smoke:
	docker compose up -d bmi-postgres $(BACKEND_SERVICE)
	docker compose exec -T $(BACKEND_SERVICE) alembic -c backend/migrations/alembic.ini upgrade head
	docker compose exec -T $(BACKEND_SERVICE) python -m backend.tests.smoke_check

cli:
	docker compose exec $(BACKEND_SERVICE) bmi $(filter-out $@,$(MAKECMDGOALS))

migrate:
	docker compose up -d bmi-postgres $(BACKEND_SERVICE)
	docker compose exec -T $(BACKEND_SERVICE) alembic -c backend/migrations/alembic.ini upgrade head

%:
	@:
