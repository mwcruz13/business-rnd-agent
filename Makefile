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
	docker compose exec -T $(BACKEND_SERVICE) pytest

test-smoke:
	docker compose up -d bmi-postgres $(BACKEND_SERVICE)
	docker compose exec -T $(BACKEND_SERVICE) python -m backend.tests.smoke_check

cli:
	docker compose exec $(BACKEND_SERVICE) bmi $(filter-out $@,$(MAKECMDGOALS))

migrate:
	docker compose up -d bmi-postgres $(BACKEND_SERVICE)
	docker compose exec -T $(BACKEND_SERVICE) alembic upgrade head

%:
	@:
