.PHONY: build up down logs test clean restart

# ─── Build all containers ────────────────────────────
build:
	docker compose build

# ─── Start all services ─────────────────────────────
up:
	docker compose up -d

# ─── Stop all services ──────────────────────────────
down:
	docker compose down

# ─── View logs (follow) ─────────────────────────────
logs:
	docker compose logs -f

# ─── View logs for a specific service ────────────────
logs-%:
	docker compose logs -f $*

# ─── Run backend tests ──────────────────────────────
test:
	docker compose exec backend python -m pytest app/tests/ -v

# ─── Restart a specific service ──────────────────────
restart-%:
	docker compose restart $*

# ─── Restart all ─────────────────────────────────────
restart:
	docker compose restart

# ─── Shell into backend container ────────────────────
shell:
	docker compose exec backend bash

# ─── Clean everything (containers + volumes) ─────────
clean:
	docker compose down -v --remove-orphans
	docker image prune -f

# ─── Full rebuild from scratch ───────────────────────
rebuild: clean build up

# ─── Copy .env.example to .env if missing ────────────
env:
	@if [ ! -f .env ]; then cp .env.example .env && echo "Created .env from .env.example"; else echo ".env already exists"; fi
