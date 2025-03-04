.PHONY: help install test run down clean

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make run      - Run the service in Docker"
	@echo "  make down     - Stop all running services"
	@echo "  make clean    - Remove all containers"

install:
	pip install -r requirements.txt

test:
	pytest

run:
	docker-compose up -d --build

down:
	docker-compose down

clean:
	docker system prune -af
