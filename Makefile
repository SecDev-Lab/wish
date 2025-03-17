# Makefile for wish project
# Runs commands across all Python projects

# Find all Python projects (directories containing pyproject.toml)
PYTHON_PROJECTS := $(dir $(shell find . -name "pyproject.toml" -not -path "*/\.*"))

.PHONY: test lint format help

# Default target
help:
	@echo "Available commands:"
	@echo "  make test    - Run tests in all Python projects"
	@echo "  make lint    - Run linting in all Python projects"
	@echo "  make format  - Format code in all Python projects"

# Run tests in all Python projects
test:
	@echo "Running tests in all Python projects..."
	@for project in $(PYTHON_PROJECTS); do \
		echo "\n=== Running tests in $$project ==="; \
		(cd $$project && uv run pytest) || echo "Tests failed in $$project"; \
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
