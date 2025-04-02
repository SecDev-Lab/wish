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

# Clean up generated files
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	find src/ -type d -name "__pycache__" -exec rm -rf {} +
