# Makefile for wish project
# Runs commands across all Python projects

# Find all Python projects (directories containing pyproject.toml)
PYTHON_PROJECTS := $(dir $(shell find . -name "pyproject.toml" -not -path "*/\.*"))

.PHONY: test integrated-test lint format e2e run-api help

# Default target
help:
	@echo "Available commands:"
	@echo "  make test            - Run unit tests in all Python projects"
	@echo "  make integrated-test - Run integration tests in projects with tests/integrated directory"
	@echo "  make lint            - Run linting in all Python projects"
	@echo "  make format          - Format code in all Python projects"
	@echo "  make e2e             - Run E2E tests for wish-log-analysis-api"
	@echo "  make run-api         - Start unified API Gateway for wish services"

# Run unit tests in all Python projects
test:
	@echo "Running unit tests in all Python projects..."
	@for project in $(PYTHON_PROJECTS); do \
		echo "\n=== Running unit tests in $$project ==="; \
		(cd $$project && uv run pytest --ignore=tests/integrated/) || echo "Unit tests failed in $$project"; \
	done

# Run integration tests only in projects with tests/integrated directory
integrated-test:
	@echo "Running integration tests in projects with tests/integrated directory..."
	@for project in $(PYTHON_PROJECTS); do \
		if [ -d "$$project/tests/integrated" ]; then \
			echo "\n=== Running integration tests in $$project ==="; \
			(cd $$project && uv run pytest tests/integrated) || echo "Integration tests failed in $$project"; \
		fi \
	done

# Run linting in all Python projects
lint:
	@echo "Running linting in all Python projects..."
	@for project in $(PYTHON_PROJECTS); do \
		echo "\n=== Running linting in $$project ==="; \
		(cd $$project && uv run ruff check) || echo "Linting failed in $$project"; \
	done

# Format code in all Python projects
format:
	@echo "Formatting code in all Python projects..."
	@for project in $(PYTHON_PROJECTS); do \
		echo "\n=== Formatting code in $$project ==="; \
		(cd $$project && uv run ruff check --fix) || echo "Formatting failed in $$project"; \
	done

# Run E2E tests for wish-log-analysis-api against a deployed API endpoint
e2e:
	@echo "Running E2E tests for wish-log-analysis-api against a deployed API endpoint..."
	@echo "Note: This command is typically called from another repository that references this one."
	@(cd wish-log-analysis-api && make e2e)

# Start unified API Gateway for wish services
run-api:
	@echo "Starting unified API Gateway for wish services..."
	@(cd wish-api && make run-api)
