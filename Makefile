# Makefile for Browser Extension OSINT Tool

.PHONY: help setup install test run dev prod clean docker-build docker-up docker-down lint format

# Default target
help:
	@echo "Browser Extension OSINT Tool - Available commands:"
	@echo "  make setup       - Run initial setup"
	@echo "  make install     - Install dependencies"
	@echo "  make test        - Run tests"
	@echo "  make run         - Run development server"
	@echo "  make dev         - Run in development mode"
	@echo "  make prod        - Run in production mode"
	@echo "  make clean       - Clean up temporary files"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up   - Start Docker containers"
	@echo "  make docker-down - Stop Docker containers"
	@echo "  make lint        - Run code linting"
	@echo "  make format      - Format code"

# Setup project
setup:
	@echo "Setting up project..."
	@chmod +x scripts/setup.sh
	@./scripts/setup.sh

# Install dependencies
install:
	@echo "Installing dependencies..."
	@pip install -r backend/requirements.txt

# Run tests
test:
	@echo "Running tests..."
	@cd backend && python -m pytest ../tests -v

# Run development server
run:
	@echo "Starting development server..."
	@cd backend && python app.py

# Development mode
dev:
	@echo "Starting in development mode..."
	@export FLASK_ENV=development && cd backend && python app.py

# Production mode
prod:
	@echo "Starting in production mode..."
	@export FLASK_ENV=production && cd backend && gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# Clean up
clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@rm -rf htmlcov/
	@rm -rf .pytest_cache/
	@echo "Cleaned up temporary files"

# Docker commands
docker-build:
	@echo "Building Docker images..."
	@cd docker && docker-compose build

docker-up:
	@echo "Starting Docker containers..."
	@cd docker && docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	@cd docker && docker-compose down

# Code quality
lint:
	@echo "Running linting..."
	@cd backend && flake8 . --max-line-length=100 --exclude=venv,__pycache__

format:
	@echo "Formatting code..."
	@cd backend && black . --line-length=100 --exclude=venv

# Database operations
db-init:
	@echo "Initializing database..."
	@cd backend && python -c "from database.manager import DatabaseManager; DatabaseManager()"

db-clean:
	@echo "Cleaning old cache entries..."
	@cd backend && python -c "from database.manager import DatabaseManager; db = DatabaseManager(); db.cleanup_old_cache()"

# Test scrapers
test-scrapers:
	@echo "Testing scrapers..."
	@python scripts/test_scrapers.py
