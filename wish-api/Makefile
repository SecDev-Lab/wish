.PHONY: deps gen-requirements build run-api deploy clean e2e

# Dependency management
deps:
	uv sync --dev
	# 両方のAPIパッケージの依存関係をインストール
	cd ../wish-command-generation-api && uv sync --dev
	cd ../wish-log-analysis-api && uv sync --dev

# Generate requirements.txt from pyproject.toml
gen-requirements: deps
	uv run ./scripts/generate_requirements.py

# Build custom Docker image for SAM
build-docker-image: gen-requirements
	@echo "Building custom SAM Docker image with Python 3.10..."
	docker build -t custom-sam-build -f Dockerfile.sam .
	@echo "Custom SAM Docker image built successfully"

# SAM build (ローカル環境で実行)
build: build-docker-image
	sam build --use-container --skip-pull-image --build-image custom-sam-build

# Start local development server (using container)
run-api: build
	uv run python scripts/env_to_json.py
	sam local start-api --env-vars .env.json

# Clean up generated files
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	rm -f requirements.txt
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Checking if custom-sam-build Docker image exists..."
	@if docker image inspect custom-sam-build >/dev/null 2>&1; then \
		echo "Removing custom-sam-build Docker image..."; \
		docker rmi custom-sam-build; \
	else \
		echo "custom-sam-build Docker image not found, skipping removal"; \
	fi

# Run E2E tests against a deployed API endpoint
e2e:
	@echo "Note: This command is typically called from another repository that references this one."
	uv run pytest tests/e2e/
