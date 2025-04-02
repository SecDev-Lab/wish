.PHONY: deps gen-requirements install-sam-deps build run-api deploy clean build-AnalyzeFunction

# Dependency management
deps:
	uv sync --dev

# Generate requirements.txt from pyproject.toml
gen-requirements: deps
	uv run ./generate_requirements.py

# Install dependencies for SAM
install-sam-deps: gen-requirements
	python3 -m pip install -r vendor/requirements.txt -t vendor/

# SAM build (using container)
build: gen-requirements
	sam build --use-container --skip-pull-image

# Start local development server (using container)
run-api: build
	sam local start-api --debug

# Deploy
deploy: build
	sam deploy

# Clean up generated files
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	find src/ -type d -name "__pycache__" -exec rm -rf {} +

# Build target for SAM (executed inside container)
build-AnalyzeFunction:
	python3 -m pip install -r vendor/requirements.txt -t $(ARTIFACTS_DIR)/
	cp -r src/wish_log_analysis_api $(ARTIFACTS_DIR)/
