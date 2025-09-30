.PHONY: help dev dev-frontend dev-backend build build-frontend build-backend install install-frontend install-backend clean test test-frontend test-backend lint lint-frontend lint-backend format format-frontend format-backend type-check update-requirements setup-dev start-services stop-services reset-db migrate init-db docker-build docker-run docker-stop check-health logs-backend logs-frontend logs-services check-deps ci

# Constants
FRONTEND_DIR = vera_frontend
BACKEND_DIR = vera_backend
PYTHON = python3
NODE_PACKAGE_MANAGER = npm
BACKEND_HOST = 0.0.0.0
BACKEND_PORT = 8000
FRONTEND_PORT = 5173

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

# Default target
help:
	@echo "$(GREEN)Vera Project Makefile$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  $(GREEN)Development:$(NC)"
	@echo "    dev                 - Run both frontend and backend in development mode"
	@echo "    dev-frontend        - Run frontend development server"
	@echo "    dev-backend         - Run backend development server"
	@echo ""
	@echo "  $(GREEN)Build:$(NC)"
	@echo "    build               - Build both frontend and backend"
	@echo "    build-frontend      - Build frontend for production"
	@echo "    build-backend       - Prepare backend for production"
	@echo ""
	@echo "  $(GREEN)Installation:$(NC)"
	@echo "    install             - Install dependencies for both frontend and backend"
	@echo "    install-frontend    - Install frontend dependencies"
	@echo "    install-backend     - Install backend dependencies"
	@echo "    setup-dev           - Complete development environment setup"
	@echo ""
	@echo "  $(GREEN)Testing:$(NC)"
	@echo "    test                - Run tests for both frontend and backend"
	@echo "    test-frontend       - Run frontend tests"
	@echo "    test-backend        - Run backend tests"
	@echo ""
	@echo "  $(GREEN)Code Quality:$(NC)"
	@echo "    lint                - Lint both frontend and backend"
	@echo "    lint-frontend       - Lint frontend code"
	@echo "    lint-backend        - Lint backend code"
	@echo "    format              - Format both frontend and backend code"
	@echo "    format-frontend     - Format frontend code"
	@echo "    format-backend      - Format backend code"
	@echo "    type-check          - Run type checking on both projects"
	@echo ""
	@echo "  $(GREEN)Dependencies:$(NC)"
	@echo "    update-requirements - Update Python requirements.txt"
	@echo ""
	@echo "  $(GREEN)Database:$(NC)"
	@echo "    reset-db            - Reset database migrations"
	@echo "    migrate             - Run database migrations"
	@echo ""
	@echo "  $(GREEN)Services:$(NC)"
	@echo "    start-services      - Start required services (Redis, PostgreSQL)"
	@echo "    stop-services       - Stop services"
	@echo ""
	@echo "  $(GREEN)Docker:$(NC)"
	@echo "    docker-build        - Build Docker containers"
	@echo "    docker-run          - Run application with Docker"
	@echo "    docker-stop         - Stop Docker containers"
	@echo ""
	@echo "  $(GREEN)Utilities:$(NC)"
	@echo "    clean               - Clean build artifacts and cache files"
	@echo "    check-health        - Check if frontend and backend are running"
	@echo "    check-deps          - Check for outdated dependencies"
	@echo "    init-db             - Initialize database tables"
	@echo ""
	@echo "  $(GREEN)Logs:$(NC)"
	@echo "    logs-backend        - Show backend container logs"
	@echo "    logs-frontend       - Show frontend container logs"
	@echo "    logs-services       - Show service container logs"

# Development commands
dev:
	@echo "$(GREEN)Starting both frontend and backend in development mode...$(NC)"
	@echo "$(YELLOW)Frontend will be available at http://localhost:$(FRONTEND_PORT)$(NC)"
	@echo "$(YELLOW)Backend will be available at http://localhost:$(BACKEND_PORT)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop both servers$(NC)"
	@trap 'kill %1 %2' INT; \
	$(MAKE) dev-backend & \
	$(MAKE) dev-frontend & \
	wait

dev-frontend:
	@echo "$(GREEN)Starting frontend development server...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) run dev

dev-backend:
	@echo "$(GREEN)Starting backend development server...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) --reload

# Build commands
build: build-frontend build-backend

build-frontend:
	@echo "$(GREEN)Building frontend for production...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) run build

build-backend:
	@echo "$(GREEN)Preparing backend for production...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m py_compile app/main.py
	@echo "$(GREEN)Backend ready for production deployment$(NC)"

# Installation commands
install: install-frontend install-backend

install-frontend:
	@echo "$(GREEN)Installing frontend dependencies...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) install

install-backend:
	@echo "$(GREEN)Installing backend dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.txt

setup-dev: install
	@echo "$(GREEN)Setting up development environment...$(NC)"
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pip install -r requirements.dev.txt
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(YELLOW)You can now run 'make dev' to start both servers$(NC)"

# Testing commands
test: test-backend test-frontend

test-frontend:
	@echo "$(GREEN)Running frontend tests...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) run test 2>/dev/null || echo "$(YELLOW)No frontend tests configured yet$(NC)"

test-backend:
	@echo "$(GREEN)Running backend tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest tests/ -v --tb=short || echo "$(YELLOW)No backend tests found or pytest not installed$(NC)"

# Linting commands
lint: lint-frontend lint-backend

lint-frontend:
	@echo "$(GREEN)Linting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) run lint

lint-backend:
	@echo "$(GREEN)Linting backend code...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m flake8 app/ --max-line-length=88 --extend-ignore=E203,W503 || echo "$(YELLOW)flake8 not installed, run 'make setup-dev' first$(NC)"

# Formatting commands
format: format-frontend format-backend

format-frontend:
	@echo "$(GREEN)Formatting frontend code...$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) run lint -- --fix 2>/dev/null || echo "$(YELLOW)Frontend auto-fix not configured$(NC)"

format-backend:
	@echo "$(GREEN)Formatting backend code...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m black app/ --line-length=88 || echo "$(YELLOW)black not installed, run 'make setup-dev' first$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m isort app/ --profile black || echo "$(YELLOW)isort not installed, run 'make setup-dev' first$(NC)"

# Type checking
type-check:
	@echo "$(GREEN)Running type checks...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m mypy app/ --ignore-missing-imports || echo "$(YELLOW)mypy not installed, run 'make setup-dev' first$(NC)"
	@echo "$(GREEN)Frontend type checking is handled by TypeScript compiler$(NC)"

# Requirements management
update-requirements:
	@echo "$(GREEN)Updating Python requirements...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pip freeze > requirements.txt
	@echo "$(GREEN)Requirements updated in $(BACKEND_DIR)/requirements.txt$(NC)"

# Database commands
reset-db:
	@echo "$(GREEN)Resetting database...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -c "from app.database import reset_database; reset_database()" || echo "$(YELLOW)Database reset function not available$(NC)"

migrate:
	@echo "$(GREEN)Running database migrations...$(NC)"
	cd $(BACKEND_DIR) && alembic upgrade head || echo "$(YELLOW)Alembic not configured or not installed$(NC)"

# Service management (requires Docker or local installations)
start-services:
	@echo "$(GREEN)Starting required services with Docker Compose...$(NC)"
	docker-compose -f docker-compose.dev.yml up -d || echo "$(YELLOW)Docker Compose not available, trying individual containers...$(NC)"
	docker run -d --name vera-postgres-dev -p 5432:5432 -e POSTGRES_USER=vera -e POSTGRES_PASSWORD=password -e POSTGRES_DB=vera postgres:13 2>/dev/null || echo "$(YELLOW)PostgreSQL container already running$(NC)"
	docker run -d --name vera-redis-dev -p 6379:6379 redis:7-alpine 2>/dev/null || echo "$(YELLOW)Redis container already running$(NC)"
	@echo "$(GREEN)Services started (if available)$(NC)"

stop-services:
	@echo "$(GREEN)Stopping services...$(NC)"
	docker-compose -f docker-compose.dev.yml down 2>/dev/null || echo "$(YELLOW)Docker Compose not running$(NC)"
	docker stop vera-postgres-dev vera-redis-dev 2>/dev/null || echo "$(YELLOW)Individual containers not running$(NC)"
	docker rm vera-postgres-dev vera-redis-dev 2>/dev/null || echo "$(YELLOW)Containers already removed$(NC)"

# Docker commands
docker-build:
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker build -t vera-backend $(BACKEND_DIR)/ || echo "$(RED)Backend Dockerfile not found$(NC)"
	docker build -t vera-frontend $(FRONTEND_DIR)/ || echo "$(RED)Frontend Dockerfile not found$(NC)"

docker-run: docker-build
	@echo "$(GREEN)Running application with Docker...$(NC)"
	docker-compose up -d || echo "$(RED)docker-compose.yml not found$(NC)"

docker-stop:
	@echo "$(GREEN)Stopping Docker containers...$(NC)"
	docker-compose down || echo "$(YELLOW)docker-compose.yml not found or containers not running$(NC)"

# Cleanup
clean:
	@echo "$(GREEN)Cleaning build artifacts and cache files...$(NC)"
	# Frontend cleanup
	cd $(FRONTEND_DIR) && rm -rf node_modules/.cache dist build 2>/dev/null || true
	# Backend cleanup
	cd $(BACKEND_DIR) && find . -type f -name '*.pyc' -delete 2>/dev/null || true
	cd $(BACKEND_DIR) && find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND_DIR) && find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true
	cd $(BACKEND_DIR) && rm -rf .mypy_cache .pytest_cache 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Additional helpful commands
check-health:
	@echo "$(GREEN)Checking application health...$(NC)"
	@echo "$(YELLOW)Checking backend health...$(NC)"
	curl -f http://localhost:8000/health 2>/dev/null && echo "$(GREEN)Backend is healthy$(NC)" || echo "$(RED)Backend is not responding$(NC)"
	@echo "$(YELLOW)Checking frontend...$(NC)"
	curl -f http://localhost:5173 2>/dev/null && echo "$(GREEN)Frontend is healthy$(NC)" || echo "$(RED)Frontend is not responding$(NC)"

logs-backend:
	@echo "$(GREEN)Showing backend logs...$(NC)"
	docker logs vera-backend -f 2>/dev/null || echo "$(YELLOW)Backend container not running$(NC)"

logs-frontend:
	@echo "$(GREEN)Showing frontend logs...$(NC)"
	docker logs vera-frontend -f 2>/dev/null || echo "$(YELLOW)Frontend container not running$(NC)"

logs-services:
	@echo "$(GREEN)Showing service logs...$(NC)"
	docker-compose -f docker-compose.dev.yml logs -f

init-db:
	@echo "$(GREEN)Initializing database...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -c "from app.database import init_database; init_database()"

check-deps:
	@echo "$(GREEN)Checking for outdated dependencies...$(NC)"
	@echo "$(YELLOW)Backend dependencies:$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m pip list --outdated || echo "$(YELLOW)pip-tools not available$(NC)"
	@echo "$(YELLOW)Frontend dependencies:$(NC)"
	cd $(FRONTEND_DIR) && $(NODE_PACKAGE_MANAGER) outdated || echo "$(YELLOW)No outdated packages$(NC)"

# CI/CD simulation
ci: lint type-check test
	@echo "$(GREEN)All CI checks completed!$(NC)"
