# MediAssist AI — Makefile
# Usage: make <target>

.PHONY: help dev build test seed ingest lint clean deploy logs stop

COMPOSE        = docker compose
COMPOSE_FILE   = docker-compose.yml
BACKEND_SVC    = backend
PYTHON         = python

help:
	@echo ""
	@echo "  MediAssist AI — available commands"
	@echo ""
	@echo "  Development"
	@echo "    make dev        Start all services (infra + backend hot-reload)"
	@echo "    make infra      Start only infra (postgres, qdrant, langfuse)"
	@echo "    make stop       Stop all containers"
	@echo "    make logs       Tail backend logs"
	@echo ""
	@echo "  Data"
	@echo "    make seed       Seed all 4 databases with sample data"
	@echo "    make ingest     Ingest medical knowledge docs into Qdrant"
	@echo "    make setup      seed + ingest (run once after first boot)"
	@echo ""
	@echo "  Frontend"
	@echo "    make frontend   Run Vue dev server (port 5173)"
	@echo "    make build-fe   Production build of frontend"
	@echo ""
	@echo "  Testing"
	@echo "    make test       Run all pytest tests"
	@echo "    make test-v     Run tests with verbose output"
	@echo "    make lint       Run ruff linter on backend/"
	@echo ""
	@echo "  Production"
	@echo "    make build      Build Docker image"
	@echo "    make deploy     Full production stack via docker compose"
	@echo "    make clean      Remove containers, volumes, and build cache"
	@echo ""

# ── Development ──────────────────────────────────────────────────────────────

dev:
	$(COMPOSE) -f infrastructure/docker-compose.yml up -d
	@echo "→ Infra running. Starting backend with hot-reload..."
	PYTHONPATH=. uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

infra:
	$(COMPOSE) -f infrastructure/docker-compose.yml up -d
	@echo "→ postgres:5432  qdrant:6333  langfuse:3000  all healthy"

stop:
	$(COMPOSE) -f infrastructure/docker-compose.yml down
	-$(COMPOSE) -f $(COMPOSE_FILE) down 2>/dev/null || true

logs:
	$(COMPOSE) logs -f $(BACKEND_SVC)

# ── Data ─────────────────────────────────────────────────────────────────────

seed:
	PYTHONPATH=. $(PYTHON) -m backend.database.seed

ingest:
	PYTHONPATH=. $(PYTHON) -m backend.rag.ingestion.pipeline ./docs/medical

setup: seed ingest
	@echo "✓ Database seeded and RAG knowledge ingested."

# ── Frontend ─────────────────────────────────────────────────────────────────

frontend:
	cd frontend && npm run dev

build-fe:
	cd frontend && npm run build

# ── Testing ──────────────────────────────────────────────────────────────────

test:
	PYTHONPATH=. pytest backend/tests/ -q

test-v:
	PYTHONPATH=. pytest backend/tests/ -v

lint:
	ruff check backend/

# ── Production ───────────────────────────────────────────────────────────────

build:
	docker build -t mediassist-ai:latest .

deploy:
	$(COMPOSE) -f $(COMPOSE_FILE) pull
	$(COMPOSE) -f $(COMPOSE_FILE) up -d --build

clean:
	$(COMPOSE) -f infrastructure/docker-compose.yml down -v --remove-orphans
	-$(COMPOSE) -f $(COMPOSE_FILE) down -v --remove-orphans 2>/dev/null || true
	docker image prune -f
	@echo "✓ Cleaned up."
