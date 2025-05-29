# Makefile for wish-tools development

.PHONY: help install test docs lint clean check-docs

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync

test: ## Run all tests
	uv run python -m pytest tests/
	uv run python scripts/test_tools.py

docs: ## Generate tool documentation
	uv run python scripts/generate_tool_docs.py
	@echo "Documentation generated in docs/tools/"

check-docs: ## Check if documentation is up to date
	@echo "Checking if documentation is up to date..."
	@uv run python scripts/generate_tool_docs.py --output-dir docs/tools-temp
	@if ! diff -r docs/tools docs/tools-temp > /dev/null 2>&1; then \
		echo "❌ Documentation is out of date. Run 'make docs' to update."; \
		rm -rf docs/tools-temp; \
		exit 1; \
	else \
		echo "✅ Documentation is up to date."; \
		rm -rf docs/tools-temp; \
	fi

lint: ## Run linting
	uv run ruff check src/ tests/ scripts/
	uv run ruff format --check src/ tests/ scripts/

format: ## Format code
	uv run ruff format src/ tests/ scripts/

clean: ## Clean up temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf docs/tools-temp/

# Development workflow targets
dev-setup: install ## Set up development environment
	@echo "Installing pre-commit hooks..."
	@uv run pre-commit install
	@echo "✅ Pre-commit hooks installed"

dev-check: lint test check-docs ## Run all development checks

# Tool development workflow
add-tool: ## Add a new tool (requires TOOL_NAME)
	@if [ -z "$(TOOL_NAME)" ]; then \
		echo "Usage: make add-tool TOOL_NAME=mytool"; \
		exit 1; \
	fi
	@echo "Creating template for tool: $(TOOL_NAME)"
	@cp scripts/tool_template.py src/wish_tools/tools/$(TOOL_NAME).py
	@sed -i '' 's/TOOL_NAME/$(TOOL_NAME)/g' src/wish_tools/tools/$(TOOL_NAME).py
	@echo "✅ Tool template created: src/wish_tools/tools/$(TOOL_NAME).py"
	@echo "Next steps:"
	@echo "1. Edit src/wish_tools/tools/$(TOOL_NAME).py"
	@echo "2. Run 'make docs' to generate documentation"
	@echo "3. Run 'make test' to verify implementation"

release-check: ## Check if ready for release
	@echo "🔍 Running release checks..."
	@make dev-check
	@echo "✅ All checks passed. Ready for release!"