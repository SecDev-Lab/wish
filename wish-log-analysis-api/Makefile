.PHONY: deps gen-requirements install-sam-deps build run-api deploy clean build-AnalyzeFunction e2e

# Dependency management
deps:
	uv sync --dev

# Generate requirements.txt from pyproject.toml
gen-requirements: deps
	uv run ./scripts/generate_requirements.py

# Install dependencies for SAM
install-sam-deps: gen-requirements
	python -m pip install -r requirements.txt -t vendor/

# SAM build (using container)
build: install-sam-deps
	sam build --use-container --skip-pull-image

# Start local development server (using container)
run-api: build
	uv run python scripts/env_to_json.py
	sam local start-api --env-vars .env.json

# Clean up generated files
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	rm -f requirements.txt
	find src/ -type d -name "__pycache__" -exec rm -rf {} +

# Run E2E tests
e2e:
	uv run pytest tests/e2e/
