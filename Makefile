# Makefile
.PHONY: help install test test-docker build run logs ps sh down clean

SERVICE ?= api

help:
	@echo "Available commands:"
	@echo "  make install      - Install deps locally (Python)"
	@echo "  make test         - Run tests locally (pytest)"
	@echo "  make build        - Build Docker image(s)"
	@echo "  make run          - Up Docker (detached) and build if needed"
	@echo "  make logs         - Follow logs from the service"
	@echo "  make ps           - Show running containers"
	@echo "  make sh           - Shell into the service container"
	@echo "  make test-docker  - Run tests inside a one-off container"
	@echo "  make down         - Stop & remove containers"
	@echo "  make clean        - Prune dangling images/containers/networks"

# --- Local (Windows) ---
install:
	@echo ">>> Checking prerequisites..."
	@python --version >/dev/null 2>&1 || { \
		echo "Python not found."; \
		echo "Windows: https://www.python.org/downloads/"; \
		echo "macOS (brew): brew install python"; \
		echo "Ubuntu/Debian: sudo apt-get install -y python3 python3-pip"; exit 1; }
	@pip --version >/dev/null 2>&1 || { \
		echo "pip not found."; \
		echo "Try: python -m ensurepip --upgrade"; exit 1; }
	@docker --version >/dev/null 2>&1 || { \
		echo "Docker not found: https://docs.docker.com/get-docker/"; exit 1; }
	@docker compose version >/dev/null 2>&1 || { \
		echo "Docker Compose v2 not found."; \
		echo "Update Docker Desktop or install compose v2"; exit 1; }
	@echo ">>> Installing Python deps..."
	python -m pip install -r requirements.txt

test:
	pytest

# --- Docker ---
build:
	docker compose build

run:
	docker compose up -d --build

logs:
	docker compose logs -f $(SERVICE)

ps:
	docker compose ps

sh:
	docker compose exec $(SERVICE) sh

test-docker:
	docker compose run --rm $(SERVICE) pytest

down:
	docker compose down

clean:
	docker system prune -af
