.PHONY: deps gen-requirements install-sam-deps test dev build deploy clean build-AnalyzeFunction

# 依存関係の管理
deps:
	uv sync --dev

# pyproject.tomlから requirements.txt を生成
gen-requirements: deps
	uv run ./generate_requirements.py

# SAM用の依存関係をインストール
install-sam-deps: gen-requirements
	python3 -m pip install -r requirements.txt -t vendor/

# テスト実行
test: deps
	uv run pytest

# ローカル開発サーバー起動
dev: install-sam-deps
	sam local start-api

# SAMビルド
build: install-sam-deps
	sam build

# デプロイ
deploy: build
	sam deploy

# 生成ファイルのクリーンアップ
clean:
	rm -rf .aws-sam
	rm -rf vendor/
	find src/ -type d -name "__pycache__" -exec rm -rf {} +
	rm -f requirements.txt

# SAM用のビルドターゲット
build-AnalyzeFunction:
	python3 -m pip install -r requirements.txt -t $(ARTIFACTS_DIR)/
	cp -r src/wish_log_analysis_api $(ARTIFACTS_DIR)/
