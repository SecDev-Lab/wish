.PHONY: deps gen-requirements install-sam-deps build run-api deploy clean build-AnalyzeFunction

# 依存関係の管理
deps:
	uv sync --dev

# pyproject.tomlから requirements.txt を生成
gen-requirements: deps
	uv run ./generate_requirements.py

# SAM用の依存関係をインストール
install-sam-deps: gen-requirements
	python3 -m pip install -r vendor/requirements.txt -t vendor/

# SAMビルド（コンテナ使用）
build: gen-requirements
	sam build --use-container --skip-pull-image

# ローカル開発サーバー起動（コンテナ使用）
run-api: build
	sam local start-api --debug

# デプロイ
deploy: build
	sam deploy

# 生成ファイルのクリーンアップ
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	find src/ -type d -name "__pycache__" -exec rm -rf {} +

# SAM用のビルドターゲット（コンテナ内で実行される）
build-AnalyzeFunction:
	python3 -m pip install -r vendor/requirements.txt -t $(ARTIFACTS_DIR)/
	cp -r src/wish_log_analysis_api $(ARTIFACTS_DIR)/
