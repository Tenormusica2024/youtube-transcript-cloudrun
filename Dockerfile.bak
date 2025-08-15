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