.PHONY: help setup dev test docker-up docker-down docker-init clean

help:
	@echo "Embedding Service - Available Commands"
	@echo "======================================="
	@echo "  make setup       - Initial project setup"
	@echo "  make dev         - Run in development mode"
	@echo "  make test        - Run tests"
	@echo "  make docker-up   - Start with Docker Compose"
	@echo "  make docker-init - Initialize after first docker-up"
	@echo "  make docker-down - Stop Docker Compose"
	@echo "  make clean       - Clean up cache and temp files"

setup:
	@echo "Setting up project..."
	cp .env.example .env
	python3 -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	./venv/bin/pip install -r requirements-dev.txt
	mkdir -p knowledge
	@echo "✓ Setup complete!"
	@echo "  Edit .env with your configuration"
	@echo "  Then run: make dev"

dev:
	@echo "Starting development server..."
	./venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	@echo "Running tests..."
	./venv/bin/pytest tests/ -v

docker-up:
	@echo "Starting services with Docker Compose..."
	cd docker && docker-compose up -d
	@echo "✓ Services started!"
	@echo ""
	@echo "⚠️  IMPORTANT: Run 'make docker-init' to complete setup"
	@echo ""
	@echo "  API: http://localhost:8000"
	@echo "  Docs: http://localhost:8000/docs"

docker-init:
	@echo "Running initialization..."
	chmod +x scripts/init.sh
	./scripts/init.sh

docker-down:
	@echo "Stopping services..."
	cd docker && docker-compose down

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f dump.rdb
	@echo "✓ Cleanup complete!"