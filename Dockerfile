# Cloud Run用Dockerfile
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システム依存関係をインストール
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 非rootユーザーを作成
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# ポート8080を公開
EXPOSE 8080

# Gunicornでアプリケーションを起動
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class sync --threads 8 --timeout 0 app:app