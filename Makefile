STAND ?= local

DEV  := docker compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml
PROD := docker compose -f infra/docker-compose.prod.yml

.PHONY: up down restart rebuild-frontend rebuild-backend migrate migrate-create seed test lint backend-dev \
        prod-up prod-down prod-restart prod-rebuild-backend prod-rebuild-frontend prod-logs prod-ps \
        help

## ── Dev ──────────────────────────────────────────────────────────────────────

up: ## Start all dev services
	$(DEV) up -d

down: ## Stop all dev services
	$(DEV) down

restart: ## Restart all dev services
	$(DEV) down && $(DEV) up -d

rebuild-frontend: ## Rebuild & restart frontend (dev)
	$(DEV) rm -fsv frontend
	$(DEV) build --no-cache frontend
	$(DEV) up -d frontend

rebuild-backend: ## Rebuild & restart backend + celery (dev)
	$(DEV) rm -fsv backend celery-worker
	$(DEV) build --no-cache backend
	$(DEV) up -d backend celery-worker

migrate: ## Run alembic migrations (dev)
	docker exec infra-backend-1 sh -c "cd /app && STAND_NAME=$(STAND) alembic upgrade head"

migrate-create: ## Create new migration: make migrate-create msg="description"
	docker exec infra-backend-1 sh -c "cd /app && STAND_NAME=$(STAND) alembic revision --autogenerate -m '$(msg)'"

seed: ## Run seed script (dev)
	docker exec infra-backend-1 sh -c "cd /app && STAND_NAME=$(STAND) python scripts/seed.py"

test: ## Run backend tests
	cd backend && STAND_NAME=test pytest -v

lint: ## Run ruff + mypy
	cd backend && ruff check . && mypy app/

backend-dev: ## Run backend locally without Docker
	cd backend && STAND_NAME=local uvicorn app.main:app --reload --port 8000

frontend-build-image: ## Build frontend Docker image (dev)
	$(DEV) build frontend

frontend-logs: ## Tail frontend logs (dev)
	$(DEV) logs -f frontend

frontend-install: ## npm install
	cd frontend && npm install

frontend-dev: ## Run frontend locally without Docker
	cd frontend && npm run dev

frontend-build: ## Build frontend for production locally
	cd frontend && npm run build

## ── Prod ─────────────────────────────────────────────────────────────────────

prod-up: ## Start all prod services (detached)
	$(PROD) up -d

prod-down: ## Stop all prod services
	$(PROD) down

prod-restart: ## Restart all prod services
	$(PROD) down && $(PROD) up -d

prod-rebuild-backend: ## Rebuild & restart backend + celery (prod, no cache)
	$(PROD) rm -fsv backend celery-worker
	$(PROD) build --no-cache backend
	$(PROD) up -d backend celery-worker

prod-rebuild-frontend: ## Rebuild & restart frontend (prod, no cache)
	$(PROD) rm -fsv frontend
	$(PROD) build --no-cache frontend
	$(PROD) up -d frontend

prod-logs: ## Tail all prod logs (Ctrl+C to stop)
	$(PROD) logs -f

prod-ps: ## Show prod container status
	$(PROD) ps

## ── help ─────────────────────────────────────────────────────────────────────

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
	/^## ──/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 4) } \
	/^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
