.PHONY: help build up down restart logs logs-api logs-web test test-watch clean prune health train predict

help:
	@echo "AFS Development Commands:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View logs from all services"
	@echo "  make logs-api     - View API logs"
	@echo "  make logs-web     - View frontend logs"
	@echo "  make test         - Run backend tests"
	@echo "  make test-watch   - Run tests in watch mode"
	@echo "  make health       - Check service health"
	@echo "  make train        - Train the model"
	@echo "  make predict      - Run sample prediction"
	@echo "  make clean        - Stop and remove containers"
	@echo "  make prune        - Deep clean (removes volumes)"

build:
	@echo "Building Docker images..."
	docker compose build

up:
	@echo "Starting all services..."
	docker compose up -d
	@echo "Services starting..."
	@echo "Frontend: http://localhost:5173"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	@echo "Stopping all services..."
	docker compose down

restart:
	@echo "Restarting all services..."
	docker compose restart

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-web:
	docker compose logs -f web

test:
	@echo "Running backend tests..."
	docker compose exec api pytest tests/ -v

test-watch:
	@echo "Running tests in watch mode..."
	docker compose exec api pytest tests/ -v --looponfail

health:
	@echo "Checking API health..."
	@curl -f http://localhost:8000/health || echo "API not responding"
	@echo ""
	@echo "Checking frontend..."
	@curl -f http://localhost:5173 > /dev/null 2>&1 && echo "Frontend is up" || echo "Frontend not responding"

train:
	@echo "Training model..."
	@curl -X POST http://localhost:8000/api/v1/train \
		-H "Content-Type: application/json" \
		-d '{"force_retrain": true}' | python -m json.tool

predict:
	@echo "Running sample prediction..."
	@curl -X POST http://localhost:8000/api/v1/predict \
		-H "Content-Type: application/json" \
		-d '{"horizon_days": 7, "store_ids": ["DXB01"], "level": "attribute"}' | python -m json.tool

clean:
	@echo "Cleaning up containers..."
	docker compose down
	@echo "Removing Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

prune:
	@echo "Deep cleaning (removes volumes)..."
	docker compose down -v
	@echo "Removing images..."
	docker compose down --rmi local
	@echo "Removing Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
