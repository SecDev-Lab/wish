# wish Makefile
# Development commands for the monorepo

.PHONY: help install test lint format clean sync build all check
.DEFAULT_GOAL := help

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)wish Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	uv sync --all-packages --dev
	@echo "$(GREEN)Dependencies installed successfully$(NC)"

sync: ## Sync dependencies (alias for install)
	@$(MAKE) install

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@$(MAKE) test-models
	@$(MAKE) test-core
	@echo "$(GREEN)Tests completed$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	uv run pytest -m "unit"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	uv run pytest -m "integration"

test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	uv run pytest --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/$(NC)"

lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	uv run ruff check packages/
	uv run mypy packages/*/src/
	@echo "$(GREEN)Linting completed$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	uv run ruff format packages/
	uv run ruff check --fix packages/
	@echo "$(GREEN)Code formatted$(NC)"

check: ## Run all quality checks (lint + test)
	@echo "$(BLUE)Running all quality checks...$(NC)"
	@$(MAKE) lint
	@$(MAKE) test
	@echo "$(GREEN)All checks passed$(NC)"

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
	rm -rf .coverage 2>/dev/null || true
	rm -rf dist/ 2>/dev/null || true
	rm -rf build/ 2>/dev/null || true
	rm -rf tmp/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup completed$(NC)"

build: ## Build all packages
	@echo "$(BLUE)Building packages...$(NC)"
	uv build --all
	@echo "$(GREEN)Build completed$(NC)"

all: ## Run complete development workflow (format + lint + test)
	@echo "$(BLUE)Running complete development workflow...$(NC)"
	@$(MAKE) format
	@$(MAKE) lint
	@$(MAKE) test
	@echo "$(GREEN)Development workflow completed successfully$(NC)"

# Package-specific commands
test-models: ## Test wish-models package only
	@echo "$(BLUE)Testing wish-models...$(NC)"
	cd packages/wish-models && uv run pytest

test-core: ## Test wish-core package only  
	@echo "$(BLUE)Testing wish-core...$(NC)"
	cd packages/wish-core && uv run pytest

test-ai: ## Test wish-ai package only
	@echo "$(BLUE)Testing wish-ai...$(NC)"
	cd packages/wish-ai && uv run pytest

test-tools: ## Test wish-tools package only
	@echo "$(BLUE)Testing wish-tools...$(NC)"
	cd packages/wish-tools && uv run pytest

test-knowledge: ## Test wish-knowledge package only
	@echo "$(BLUE)Testing wish-knowledge...$(NC)"
	cd packages/wish-knowledge && uv run pytest

test-c2: ## Test wish-c2 package only
	@echo "$(BLUE)Testing wish-c2...$(NC)"
	cd packages/wish-c2 && uv run pytest

test-cli: ## Test wish-cli package only
	@echo "$(BLUE)Testing wish-cli...$(NC)"
	cd packages/wish-cli && uv run pytest

e2e: ## Run end-to-end tests (all levels, excluding live tests)
	@echo "$(BLUE)Running E2E tests...$(NC)"
	uv run pytest e2e-tests/ -m "not live" -v
	@echo "$(GREEN)E2E tests completed$(NC)"

e2e-component: ## Run component integration tests (Level 1)
	@echo "$(BLUE)Running component integration tests...$(NC)"
	uv run pytest e2e-tests/component/ -v

e2e-workflow: ## Run workflow integration tests (Level 2)
	@echo "$(BLUE)Running workflow integration tests...$(NC)"
	uv run pytest e2e-tests/workflows/ -v

e2e-scenario: ## Run scenario-based tests (Level 3)
	@echo "$(BLUE)Running scenario-based tests...$(NC)"
	uv run pytest e2e-tests/scenarios/ -v

e2e-quality: ## Run AI quality validation tests
	@echo "$(BLUE)Running AI quality tests...$(NC)"
	uv run pytest e2e-tests/quality/ -v

e2e-live-check: ## Check if live E2E environment is ready
	@echo "$(BLUE)Checking live E2E environment...$(NC)"
	@uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::test_live_environment_setup -v

e2e-live: ## Run live E2E tests against real targets (requires VPN)
	@echo "$(YELLOW)WARNING: This will run tests against real targets!$(NC)"
	@echo "$(YELLOW)Make sure you have proper authorization and VPN connection.$(NC)"
	@printf "Continue? (y/N) "; \
	read REPLY; \
	case $$REPLY in \
		[Yy]*) \
			echo "$(BLUE)Running live E2E tests...$(NC)"; \
			if uv run pytest e2e-tests/ -m "live" -v -s; then \
				echo "$(GREEN)Live E2E tests completed successfully$(NC)"; \
			else \
				echo "$(RED)Live E2E tests failed$(NC)"; \
				exit 1; \
			fi;; \
		*) \
			echo "$(RED)Aborted$(NC)";; \
	esac

e2e-tui: ## Run minimal TUI-specific tests
	@echo "$(BLUE)Running TUI-specific tests...$(NC)"
	uv run pytest e2e-tests/tui/ -v -m "tui"

# Development utilities
dev-setup: ## Setup development environment from scratch
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@$(MAKE) clean
	@$(MAKE) install
	@echo "$(GREEN)Development environment ready$(NC)"

validate: ## Validate project structure and dependencies
	@echo "$(BLUE)Validating project structure...$(NC)"
	@test -d packages/wish-models || (echo "$(RED)Missing wish-models package$(NC)" && exit 1)
	@test -d packages/wish-core || (echo "$(RED)Missing wish-core package$(NC)" && exit 1)
	@test -d packages/wish-ai || (echo "$(RED)Missing wish-ai package$(NC)" && exit 1)
	@test -d packages/wish-tools || (echo "$(RED)Missing wish-tools package$(NC)" && exit 1)
	@test -d packages/wish-knowledge || (echo "$(RED)Missing wish-knowledge package$(NC)" && exit 1)
	@test -d packages/wish-c2 || (echo "$(RED)Missing wish-c2 package$(NC)" && exit 1)
	@test -d packages/wish-cli || (echo "$(RED)Missing wish-cli package$(NC)" && exit 1)
	@echo "$(GREEN)Project structure validated$(NC)"

# CI/CD related commands
ci: ## Run CI pipeline locally
	@echo "$(BLUE)Running CI pipeline...$(NC)"
	@$(MAKE) clean
	@$(MAKE) install
	@$(MAKE) check
	@$(MAKE) build
	@echo "$(GREEN)CI pipeline completed$(NC)"

# Quick development commands
quick-test: ## Quick test (no coverage)
	uv run pytest --no-cov -x

watch-test: ## Watch tests (requires entr: apt-get install entr)
	find packages/ -name "*.py" | entr -c make quick-test