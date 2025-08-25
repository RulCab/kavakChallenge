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
