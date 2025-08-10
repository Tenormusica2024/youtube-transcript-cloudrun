# Requirements and Configuration Files

## requirements.txt
```txt
# Web Framework
Flask==2.3.3
flask-cors==4.0.0

# YouTube関連
google-api-python-client==2.100.0
google-auth==2.23.0
google-auth-httplib2==0.1.1
youtube-transcript-api==1.2.2

# Gemini AI
google-genai==1.29.0

# 環境変数管理
python-dotenv==1.0.0

# 本番サーバー
gunicorn==21.2.0

# ユーティリティ
requests==2.31.0

# オプション: Claude AI統合（将来の拡張用）
# anthropic==0.7.0
```

## Dockerfile
```dockerfile
# Python 3.10 slimイメージを使用（軽量化）
FROM python:3.10-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルのコピーと インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# 非rootユーザーの作成（セキュリティ向上）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Runが使用する環境変数PORTを受け入れる
ENV PORT=8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health')" || exit 1

# Gunicornで本番環境向けに起動
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

## cloudbuild.yaml
```yaml
# Cloud Build configuration for YouTube Transcript App
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'youtube-transcript'
      - '--image'
      - 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID'
      - '--region'
      - 'asia-northeast1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--port'
      - '8080'
      - '--memory'
      - '512Mi'
      - '--timeout'
      - '300s'
      - '--max-instances'
      - '10'
      - '--set-env-vars'
      - 'YOUTUBE_API_KEY=$$YOUTUBE_API_KEY,GEMINI_API_KEY=$$GEMINI_API_KEY'

# Store images in Google Container Registry
images:
  - 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID'

# Configuration for build
options:
  logging: CLOUD_LOGGING_ONLY
```

## .gitignore
```txt
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Distribution / packaging
dist/
build/
*.egg-info/
```

## 環境変数設定 (.env)
```env
# YouTube Data API Key
YOUTUBE_API_KEY=[REDACTED_FOR_SECURITY]

# Gemini API Key
GEMINI_API_KEY=[REDACTED_FOR_SECURITY]
```