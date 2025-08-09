# YouTube Transcript Webapp - Cloud Run版実装計画

## 現在の問題点
1. **ポート干渉**: localhost:5002が既に使用中（Claude Web App）
2. **複数サービスの競合**: 同一ポートでの複数アプリ実行による衝突
3. **動的URL問題**: Cloudflared tunnelのURL変更による不安定性

## Cloud Run版のアーキテクチャ

### メリット
- ✅ **固定URL**: `https://[project-name].run.app` で常に同じURL
- ✅ **ポート干渉なし**: Googleのインフラが自動管理
- ✅ **自動スケーリング**: 負荷に応じて自動でスケール
- ✅ **HTTPSデフォルト**: 証明書管理不要
- ✅ **他サービスと独立**: ローカル環境と完全分離

### 必要な変更点

#### 1. app.py の修正
```python
import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS  # CORSサポート追加

app = Flask(__name__)
CORS(app)  # Cloud Runでのクロスオリジン対応

# ポート設定をCloud Run対応に
PORT = int(os.environ.get('PORT', 8080))  # Cloud Runは$PORTを使用

# APIキー取得をSecret Manager対応に
def get_api_key():
    # 優先順位: 環境変数 → Secret Manager → .env
    return os.environ.get('YOUTUBE_API_KEY')

if __name__ == '__main__':
    # Cloud Run用の起動設定
    app.run(host='0.0.0.0', port=PORT, debug=False)
```

#### 2. Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 依存関係のインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルのコピー
COPY . .

# Cloud Runのポート環境変数を使用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

#### 3. requirements.txt
```
Flask==2.3.3
flask-cors==4.0.0
google-api-python-client==2.100.0
youtube-transcript-api==0.6.1
python-dotenv==1.0.0
gunicorn==21.2.0
anthropic==0.7.0
```

#### 4. .gcloudignore
```
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.env
.venv
venv/
env/
*.log
.vscode/
.idea/
```

## デプロイ手順

### 1. Google Cloud初期設定
```bash
# プロジェクト作成（一度だけ）
gcloud projects create youtube-transcript-app-2024

# プロジェクト設定
gcloud config set project youtube-transcript-app-2024

# Cloud RunとSecret Manager APIを有効化
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Secret Manager設定（APIキー保護）
```bash
# APIキーをSecret Managerに保存
echo -n "YOUR_YOUTUBE_API_KEY" | gcloud secrets create youtube-api-key --data-file=-

# Cloud Runサービスアカウントに権限付与
gcloud secrets add-iam-policy-binding youtube-api-key \
    --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
```

### 3. Cloud Runへのデプロイ
```bash
# ビルドとデプロイ（一括実行）
gcloud run deploy youtube-transcript-webapp \
    --source . \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --set-env-vars="YOUTUBE_API_KEY=YOUR_KEY" \
    --memory 512Mi \
    --cpu 1
```

### 4. 固定URLの取得
```
デプロイ完了後:
https://youtube-transcript-webapp-[hash]-an.a.run.app
```

## ローカル開発環境の分離

### docker-compose.yml（ローカルテスト用）
```yaml
version: '3.8'
services:
  youtube-app:
    build: .
    ports:
      - "8081:8080"  # ポート8081を使用（干渉回避）
    environment:
      - PORT=8080
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
    volumes:
      - .:/app
```

### ローカルテスト
```bash
# Docker Composeで起動
docker-compose up

# ブラウザでアクセス
http://localhost:8081
```

## 環境変数管理

### .env.example
```bash
# YouTube Data API
YOUTUBE_API_KEY=your_youtube_api_key_here

# Anthropic API (オプション)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Cloud Run設定
GCP_PROJECT_ID=youtube-transcript-app-2024
GCP_REGION=asia-northeast1
```

## 監視とログ

### Cloud Loggingの活用
```python
import logging
import google.cloud.logging

# Cloud Loggingクライアントの初期化
client = google.cloud.logging.Client()
client.setup_logging()

# 標準のloggingを使用
logging.info("YouTube transcript extraction started")
```

## トラブルシューティング

### よくある問題と解決策

1. **ポート設定エラー**
   - 環境変数 `$PORT` を必ず使用
   - ハードコードされたポート番号を避ける

2. **メモリ不足**
   - Cloud Runのメモリを512Mi以上に設定
   - 大きな動画の処理時は1Giに増やす

3. **タイムアウト**
   - Cloud Runのタイムアウトを300秒に設定
   - 長時間処理はCloud Tasksで非同期化

4. **CORS エラー**
   - flask-corsを適切に設定
   - 特定のドメインのみ許可する

## 次のステップ

1. ✅ Dockerfileとrequirements.txt作成
2. ✅ app.pyのCloud Run対応修正
3. ✅ GCPプロジェクト作成とAPI有効化
4. ✅ Secret Manager設定
5. ✅ Cloud Runデプロイ
6. ✅ 固定URL確認とテスト

## 参考リンク
- [Cloud Run公式ドキュメント](https://cloud.google.com/run/docs)
- [Flask on Cloud Run](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/python)
- [Secret Manager統合](https://cloud.google.com/run/docs/configuring/secrets)