# EasyApt Healthcare Scheduling System - Makefile
#
# Build automation for development, testing, and deployment
#
# Usage:
#   make setup      - Initial project setup
#   make test       - Run integration tests
#   make dev        - Start development server
#   make deploy     - Deploy to production
#   make clean      - Clean build artifacts
#   make help       - Show this help message

.PHONY: help setup test dev deploy clean install-deps check-env

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m

# Project directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
VENV_DIR := $(BACKEND_DIR)/venv
PYTHON := python3
PIP := $(PYTHON) -m pip
PYTEST := $(PYTHON) -m pytest

# Deployment configuration
DEPLOY_SERVER ?= root@192.241.146.169
DEPLOY_PATH := /root/EasyApt-main

################################################################################
# Help
################################################################################

help: ## Show this help message
	@echo "$(BLUE)EasyApt Build System$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make setup    # Initial project setup"
	@echo "  make test     # Run all tests"
	@echo "  make dev      # Start development server"

################################################################################
# Setup & Installation
################################################################################

setup: check-env install-deps ## Complete project setup
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  make test   - Run tests"
	@echo "  make dev    - Start development server"

check-env: ## Check prerequisites
	@echo "$(BLUE)Checking prerequisites...$(NC)"
	@command -v python3 >/dev/null 2>&1 || { echo "$(RED)✗ python3 not found$(NC)"; exit 1; }
	@command -v pip3 >/dev/null 2>&1 || { echo "$(RED)✗ pip3 not found$(NC)"; exit 1; }
	@echo "$(GREEN)✓ All prerequisites installed$(NC)"

$(VENV_DIR): ## Create Python virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	cd $(BACKEND_DIR) && python3 -m venv venv
	@echo "$(GREEN)✓ Virtual environment created$(NC)"

install-deps: $(VENV_DIR) ## Install Python dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install --upgrade pip --quiet
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt --quiet
	$(PIP) install pyotp qrcode pillow pytest pytest-asyncio --quiet
	@echo "$(GREEN)✓ Dependencies installed$(NC)"
	@if [ -f "$(BACKEND_DIR)/.env" ]; then \
		echo "$(GREEN)✓ .env file exists$(NC)"; \
	else \
		echo "$(YELLOW)⚠ .env file not found$(NC)"; \
	fi

################################################################################
# Testing
################################################################################

test: $(VENV_DIR) ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) tests/test_integration.py -v
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-verbose: $(VENV_DIR) ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose mode)...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) tests/test_integration.py -vv

test-coverage: $(VENV_DIR) ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	cd $(BACKEND_DIR) && $(PYTEST) tests/test_integration.py --cov=app --cov-report=html
	@echo "$(GREEN)✓ Coverage report: $(BACKEND_DIR)/htmlcov/index.html$(NC)"

################################################################################
# Development
################################################################################

dev: $(VENV_DIR) ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	@echo "$(GREEN)Backend: http://localhost:8000$(NC)"
	@echo "$(GREEN)API Docs: http://localhost:8000/docs$(NC)"
	@echo ""
	@echo "Press Ctrl+C to stop"
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-https: $(VENV_DIR) ## Start development server with HTTPS
	@echo "$(BLUE)Starting HTTPS development server...$(NC)"
	@echo "$(GREEN)Backend: https://localhost:8000$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
		--ssl-keyfile=key.pem --ssl-certfile=cert.pem

kill-dev: ## Stop development server
	@echo "$(BLUE)Stopping development server...$(NC)"
	@pkill -f uvicorn || echo "$(YELLOW)No running server found$(NC)"

################################################################################
# Database
################################################################################

db-backup: ## Create manual database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) backup_database.py
	@echo "$(GREEN)✓ Backup complete$(NC)"

db-shell: ## Open SQLite database shell
	@echo "$(BLUE)Opening database shell...$(NC)"
	sqlite3 $(BACKEND_DIR)/easyapt.db

db-info: ## Show database information
	@echo "$(BLUE)Database Information:$(NC)"
	@echo "Size: $$(du -h $(BACKEND_DIR)/easyapt.db | cut -f1)"
	@sqlite3 $(BACKEND_DIR)/easyapt.db "SELECT name FROM sqlite_master WHERE type='table';" | \
		awk '{printf "  Table: %s\n", $$0}'

################################################################################
# Monitoring
################################################################################

monitor-compliance: $(VENV_DIR) ## Run compliance monitoring
	@echo "$(BLUE)Running compliance check...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) compliance_monitor.py

monitor-operations: $(VENV_DIR) ## Run operations monitoring
	@echo "$(BLUE)Running operations check...$(NC)"
	cd $(BACKEND_DIR) && $(PYTHON) operations_monitor.py

logs-backup: ## View backup logs
	@tail -50 $(BACKEND_DIR)/backup_log.txt

logs-compliance: ## View compliance logs
	@tail -30 $(BACKEND_DIR)/compliance_log.txt

logs-operations: ## View operations logs
	@tail -30 $(BACKEND_DIR)/operations_log.txt

################################################################################
# Deployment
################################################################################

deploy: ## Deploy to production server
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "Target: $(DEPLOY_SERVER)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "$(BLUE)Creating deployment package...$(NC)"
	zip -r deploy.zip . -x "*/venv/*" "*/__pycache__/*" "*.pyc" ".git/*" > /dev/null
	@echo "$(BLUE)Uploading to server...$(NC)"
	scp deploy.zip $(DEPLOY_SERVER):$(DEPLOY_PATH)/
	@echo "$(BLUE)Installing on server...$(NC)"
	ssh $(DEPLOY_SERVER) "cd $(DEPLOY_PATH) && \
		unzip -o deploy.zip && \
		cd backend && \
		python3 -m venv venv && \
		venv/bin/pip install -r requirements.txt && \
		venv/bin/pip install pyotp qrcode pillow && \
		systemctl restart easyapt"
	@rm deploy.zip
	@echo "$(GREEN)✓ Deployment complete!$(NC)"

deploy-frontend: ## Deploy only frontend
	@echo "$(BLUE)Deploying frontend...$(NC)"
	rsync -avz --delete $(FRONTEND_DIR)/ $(DEPLOY_SERVER):$(DEPLOY_PATH)/frontend/
	ssh $(DEPLOY_SERVER) "systemctl reload nginx"
	@echo "$(GREEN)✓ Frontend deployed$(NC)"

deploy-status: ## Check deployment status
	@echo "$(BLUE)Checking server status...$(NC)"
	@ssh $(DEPLOY_SERVER) "systemctl status easyapt --no-pager"

################################################################################
# Cleanup
################################################################################

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find $(BACKEND_DIR) -type f -name "*.pyc" -delete
	rm -rf $(BACKEND_DIR)/.pytest_cache
	@echo "$(GREEN)✓ Cleaned$(NC)"

clean-all: clean ## Clean everything including venv
	@echo "$(YELLOW)This will remove the virtual environment$(NC)"
	@read -p "Continue? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -rf $(VENV_DIR)
	@echo "$(GREEN)✓ All artifacts removed$(NC)"

################################################################################
# Utilities
################################################################################

install-cron: ## Install cron jobs for automated tasks
	@echo "$(BLUE)Installing cron jobs...$(NC)"
	@(crontab -l 2>/dev/null; cat $(BACKEND_DIR)/crontab.txt) | crontab -
	@echo "$(GREEN)✓ Cron jobs installed$(NC)"
	@crontab -l

check-deps: $(VENV_DIR) ## Check for outdated dependencies
	@echo "$(BLUE)Checking for outdated packages...$(NC)"
	$(PIP) list --outdated

freeze: $(VENV_DIR) ## Update requirements.txt
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	$(PIP) freeze > $(BACKEND_DIR)/requirements.txt
	@echo "$(GREEN)✓ requirements.txt updated$(NC)"

.PHONY: all
all: setup test ## Setup and run tests
	@echo "$(GREEN)✓ Build complete$(NC)"
