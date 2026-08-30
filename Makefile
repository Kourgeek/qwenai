# ============================================================
# HyperScale Marketplace — Makefile
# ============================================================
#
# Quick commands for development, testing, and deployment.
#
# Usage:
#   make up              Start all services
#   make down            Stop all services
#   make restart         Restart all services
#   make logs [service=] View logs (optionally filter by service)
#   make test [service=] Run tests (optionally for a specific service)
#   make lint [service=] Run linter (optionally for a specific service)
#   make migrate [service=] Run migrations (optionally for a specific service)
#   make build [service=] Build service image (optionally for a specific service)
#   make clean           Remove containers, volumes, images
#   make health          Check all service health
#   make docs            Generate API docs
#   make bash [service=] Open bash in container
#
# Examples:
#   make logs service=auth-service
#   make test service=catalog-service
#   make build service=payment-service
#   make bash service=gateway
# ============================================================

# Configuration
COMPOSE_FILE := unified-docker-compose.yml
COMPOSE_CMD := docker compose -f $(COMPOSE_FILE)
PROFILE := all
PYTHON_VERSION ?= 3.12
SERVICES := auth-service user-service catalog-service cart-service \
             order-service payment-service notification-service \
             search-service seller-service admin-service bff-service gateway

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
CYAN   := \033[0;36m
NC     := \033[0m # No Color

# Default target
.PHONY: all up down restart logs test lint migrate build clean health docs bash help

help:
	@echo -e "$(CYAN)========================================$(NC)"
	@echo -e "$(CYAN)  HyperScale Marketplace — Makefile Help$(NC)"
	@echo -e "$(CYAN)========================================$(NC)"
	@echo ""
	@echo -e "$(GREEN)Infrastructure Management:$(NC)"
	@echo -e "  $(YELLOW)make up$(NC)                Start all services"
	@echo -e "  $(YELLOW)make down$(NC)             Stop all services"
	@echo -e "  $(YELLOW)make restart$(NC)          Restart all services"
	@echo -e "  $(YELLOW)make start-infra$(NC)      Start infrastructure only"
	@echo -e "  $(YELLOW)make start-services$(NC)   Start application services only"
	@echo -e "  $(YELLOW)make start-monitoring$(NC) Start monitoring only"
	@echo -e "  $(YELLOW)make start-dev$(NC)        Start dev infrastructure only"
	@echo ""
	@echo -e "$(GREEN)Development:$(NC)"
	@echo -e "  $(YELLOW)make logs [service=X]$(NC) View logs (optionally filter by service)"
	@echo -e "  $(YELLOW)make bash [service=X]$(NC) Open bash in container"
	@echo -e "  $(YELLOW)make docs$(NC)             Generate API docs"
	@echo ""
	@echo -e "$(GREEN)Code Quality:$(NC)"
	@echo -e "  $(YELLOW)make test [service=X]$(NC) Run tests (optionally for a specific service)"
	@echo -e "  $(YELLOW)make lint [service=X]$(NC) Run linter (optionally for a specific service)"
	@echo -e "  $(YELLOW)make migrate [service=X]$(NC) Run migrations (optionally for a specific service)"
	@echo ""
	@echo -e "$(GREEN)Build & Deploy:$(NC)"
	@echo -e "  $(YELLOW)make build [service=X]$(NC) Build service image (optionally for a specific service)"
	@echo -e "  $(YELLOW)make push [service=X]$(NC) Push service image to registry"
	@echo ""
	@echo -e "$(GREEN)Maintenance:$(NC)"
	@echo -e "  $(YELLOW)make clean$(NC)           Remove containers, volumes, images"
	@echo -e "  $(YELLOW)make health$(NC)          Check all service health"
	@echo -e "  $(YELLOW)make ps$(NC)              List running containers"
	@echo -e "  $(YELLOW)make top$(NC)             Show resource usage"
	@echo ""
	@echo -e "$(GREEN)Service List:$(NC)"
	@echo "  $(SERVICES)"
	@echo ""

# ============================================================
# Infrastructure Management
# ============================================================

up:
	@echo -e "$(GREEN)>>> Starting all services...$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) up -d
	@echo -e "$(GREEN)>>> All services started.$(NC)"

down:
	@echo -e "$(YELLOW)>>> Stopping all services...$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) down
	@echo -e "$(GREEN)>>> All services stopped.$(NC)"

restart:
	@echo -e "$(YELLOW)>>> Restarting all services...$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) restart
	@echo -e "$(GREEN)>>> All services restarted.$(NC)"

start-infra:
	@echo -e "$(GREEN)>>> Starting infrastructure only...$(NC)"
	@$(COMPOSE_CMD) --profile infra up -d
	@echo -e "$(GREEN)>>> Infrastructure started.$(NC)"

start-services:
	@echo -e "$(GREEN)>>> Starting application services...$(NC)"
	@$(COMPOSE_CMD) --profile services up -d
	@echo -e "$(GREEN)>>> Application services started.$(NC)"

start-monitoring:
	@echo -e "$(GREEN)>>> Starting monitoring stack...$(NC)"
	@$(COMPOSE_CMD) --profile monitoring up -d
	@echo -e "$(GREEN)>>> Monitoring stack started.$(NC)"

start-dev:
	@echo -e "$(GREEN)>>> Starting dev infrastructure...$(NC)"
	@$(COMPOSE_CMD) --profile dev up -d
	@echo -e "$(GREEN)>>> Dev infrastructure started.$(NC)"

# ============================================================
# Logs
# ============================================================

logs:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Logs for $(service)...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) logs -f --tail=200 $(service); \
	else \
		echo -e "$(GREEN)>>> All service logs...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) logs -f --tail=100; \
	fi

# ============================================================
# Testing
# ============================================================

test:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Running tests for $(service)...$(NC)"; \
		cd migration_plan/$(service) && python -m pytest tests/ -v --cov=src --cov-report=term-missing; \
	else \
		echo -e "$(GREEN)>>> Running tests for all services...$(NC)"; \
		for svc in $(SERVICES); do \
			echo -e "\n$(CYAN)>>> Testing $$svc...$(NC)"; \
			cd migration_plan/$$svc && python -m pytest tests/ -v --cov=src --cov-report=term-missing || echo -e "$(RED)>>> Tests failed for $$svc$(NC)"; \
			cd ../..; \
		done \
	fi

# ============================================================
# Linting
# ============================================================

lint:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Linting $(service)...$(NC)"; \
		cd migration_plan/$(service) && python -m ruff check src/ tests/ && python -m ruff format --check .; \
	else \
		echo -e "$(GREEN)>>> Linting all services...$(NC)"; \
		for svc in $(SERVICES); do \
			echo -e "\n$(CYAN)>>> Linting $$svc...$(NC)"; \
			cd migration_plan/$$svc && python -m ruff check src/ tests/ && python -m ruff format --check . || echo -e "$(RED)>>> Linting issues in $$svc$(NC)"; \
			cd ../..; \
		done \
	fi

# ============================================================
# Migrations
# ============================================================

migrate:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Running migrations for $(service)...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) exec $(service) alembic upgrade head; \
	else \
		echo -e "$(GREEN)>>> Running migrations for all services...$(NC)"; \
		for svc in $(SERVICES); do \
			echo -e "\n$(CYAN)>>> Migrating $$svc...$(NC)"; \
			$(COMPOSE_CMD) --profile $(PROFILE) exec $$svc alembic upgrade head || echo -e "$(YELLOW)>>> No migrations for $$svc$(NC)"; \
		done \
	fi

# ============================================================
# Build
# ============================================================

build:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Building $(service)...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) build $(service); \
	else \
		echo -e "$(GREEN)>>> Building all services...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) build; \
	fi

push:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Pushing $(service)...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) push $(service); \
	else \
		echo -e "$(GREEN)>>> Pushing all services...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) push; \
	fi

# ============================================================
# Maintenance
# ============================================================

clean:
	@echo -e "$(YELLOW)>>> Cleaning up...$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) down -v --remove-orphans
	@echo -e "$(YELLOW)>>> Removing dangling images...$(NC)"
	@docker image prune -f
	@echo -e "$(GREEN)>>> Cleanup complete.$(NC)"

health:
	@echo -e "$(GREEN)>>> Checking service health...$(NC)"
	@echo ""
	@for svc in $(SERVICES); do \
		status=$$($(COMPOSE_CMD) --profile $(PROFILE) inspect --format='{{.State.Health.Status}}' $$svc 2>/dev/null || echo "unknown"); \
		if [ "$$status" = "healthy" ]; then \
			echo -e "  $(GREEN)✓ $$svc: healthy$(NC)"; \
		elif [ "$$status" = "starting" ]; then \
			echo -e "  $(YELLOW)○ $$svc: starting$(NC)"; \
		else \
			echo -e "  $(RED)✗ $$svc: $$status$(NC)"; \
		fi; \
	done
	@echo ""
	@echo -e "$(GREEN)>>> Infrastructure:$(NC)"
	@for infra in postgres redis elasticsearch kafka zookeeper prometheus grafana; do \
		status=$$($(COMPOSE_CMD) --profile $(PROFILE) inspect --format='{{.State.Health.Status}}' $$infra 2>/dev/null || echo "unknown"); \
		if [ "$$status" = "healthy" ]; then \
			echo -e "  $(GREEN)✓ $$infra: healthy$(NC)"; \
		else \
			echo -e "  $(RED)✗ $$infra: $$status$(NC)"; \
		fi; \
	done

docs:
	@echo -e "$(GREEN)>>> Generating API documentation...$(NC)"
	@for svc in $(SERVICES); do \
		if [ -d "migration_plan/$$svc/src" ]; then \
			echo -e "\n$(CYAN)>>> Docs for $$svc...$(NC)"; \
			cd migration_plan/$$svc && \
			if command -v gradio &> /dev/null; then \
				echo "  Generating with gradio..."; \
			fi; \
			if [ -d "docs" ]; then \
				echo "  Docs directory exists"; \
			else \
				echo "  No docs directory found"; \
			fi; \
			cd ../..; \
		fi; \
	done
	@echo -e "$(GREEN)>>> API docs generation complete.$(NC)"

bash:
	@if [ -n "$(service)" ]; then \
		echo -e "$(GREEN)>>> Opening bash in $(service)...$(NC)"; \
		$(COMPOSE_CMD) --profile $(PROFILE) exec $(service) bash; \
	else \
		echo -e "$(RED)>>> Please specify a service: make bash service=<name>$(NC)"; \
		echo -e "$(YELLOW)>>> Available services: $(SERVICES)$(NC)"; \
		exit 1; \
	fi

ps:
	@echo -e "$(GREEN)>>> Running containers:$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) ps

top:
	@echo -e "$(GREEN)>>> Resource usage:$(NC)"
	@$(COMPOSE_CMD) --profile $(PROFILE) top
