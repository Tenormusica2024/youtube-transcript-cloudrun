# 🔑 本番環境 API キー設定ガイド

## 🚨 重要なセキュリティ注意事項

**⚠️ 古いAPIキーは既に公開されているため、以下のキーを即座に無効化してください：**
- `AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw`
- `AIzaSyBC8mkp2FgNXRaFLerpgjMaLG4ri4-X25A`
- `AIzaSyBKVL0MW3hbTFX7llfbuF0TL73SKNR2Rfw`

## 🔐 新しいAPIキーの作成手順

### ステップ 1: Google Cloud Console にアクセス
1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. プロジェクトを選択（既存または新規作成）

### ステップ 2: APIs & Services の設定
```bash
# CLIで有効化する場合：
gcloud services enable youtube.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

または Web UI で：
1. **APIs & Services** → **Library** に移動
2. **YouTube Data API v3** を検索して有効化
3. **Cloud Run API** を有効化
4. **Secret Manager API** を有効化（推奨）

### ステップ 3: APIキーの作成
1. **APIs & Services** → **Credentials** に移動
2. **+ CREATE CREDENTIALS** → **API key** を選択
3. 新しいAPIキーが生成される

### ステップ 4: APIキーの制限設定（重要）
1. 作成されたAPIキーの **Edit** をクリック
2. **Application restrictions** を設定：
   - **HTTP referrers (web sites)** を選択
   - 許可するドメインを追加（例：`*.googleusercontent.com/*`、`yourdomain.com/*`）
3. **API restrictions** を設定：
   - **Restrict key** を選択
   - **YouTube Data API v3** のみを選択
4. **SAVE** をクリック

## 🚀 Cloud Run での設定方法

### Option A: 環境変数（開発・テスト環境）

```bash
# デプロイ時に環境変数として設定
gcloud run deploy youtube-transcript-secure \
  --source . \
  --region asia-northeast1 \
  --set-env-vars YOUTUBE_API_KEY="YOUR_NEW_API_KEY_HERE"
```

### Option B: Secret Manager（本番環境推奨）

```bash
# 1. Secretを作成
echo "YOUR_NEW_API_KEY_HERE" | gcloud secrets create youtube-api-key --data-file=-

# 2. Cloud Runサービスアカウントに権限付与
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding youtube-api-key \
  --member="serviceAccount:${PROJECT_ID}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. アプリケーションコードでSecret Manager から取得
# (アプリケーションが自動的にSecret Managerから読み取り)
```

## 📱 アプリケーション設定の更新

### 環境変数での設定確認
```python
import os

# アプリケーション内でのAPIキー取得
def get_youtube_api_key():
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        raise ValueError("YouTube APIキーが設定されていません")
    return api_key
```

### Secret Manager 連携（推奨）
```python
from google.cloud import secretmanager

def get_api_key_from_secret_manager():
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    secret_name = f"projects/{project_id}/secrets/youtube-api-key/versions/latest"
    
    response = client.access_secret_version(request={"name": secret_name})
    return response.payload.data.decode("UTF-8")
```

## 🔍 セキュリティ設定の確認

### APIキーの制限状況確認
```bash
# Google Cloud CLI で確認
gcloud alpha services api-keys list
gcloud alpha services api-keys describe KEY_ID
```

### 使用量とクォータの監視
```bash
# API使用量確認
gcloud logging read \
  'protoPayload.serviceName="youtube.googleapis.com"' \
  --limit=10 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName)"
```

## 📊 本番環境での推奨設定

### 1. APIキー制限
```yaml
Application restrictions:
  - HTTP referrers: 
    - "https://your-cloud-run-service-*.run.app/*"
    - "https://yourdomain.com/*"

API restrictions:
  - YouTube Data API v3 のみ

Usage quotas:
  - Queries per day: 10,000 (必要に応じて調整)
  - Queries per 100 seconds: 100
```

### 2. Cloud Run サービス設定
```yaml
Service Configuration:
  CPU: 1 vCPU
  Memory: 512 MiB
  Timeout: 300s
  Min instances: 0
  Max instances: 10
  Concurrency: 100
```

### 3. セキュリティヘッダー
```python
# アプリケーションに追加推奨
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

## 🚨 セキュリティ監視

### 1. Cloud Monitoring アラート設定
```bash
# API使用量アラート
gcloud alpha monitoring policies create \
  --policy-from-file=api-usage-alert-policy.yaml
```

### 2. ログ監視
```bash
# 異常なAPIリクエストの監視
gcloud logging sinks create youtube-api-audit \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/security_logs \
  --log-filter='protoPayload.serviceName="youtube.googleapis.com"'
```

## ✅ セットアップ完了チェックリスト

- [ ] 古いAPIキーを無効化
- [ ] 新しいAPIキーを作成・制限設定
- [ ] Cloud Run にAPIキーを安全に設定
- [ ] デプロイ・動作テスト完了
- [ ] セキュリティ監視設定
- [ ] APIクォータ制限確認
- [ ] ドキュメント更新

## 🆘 トラブルシューティング

### APIキーエラー
```bash
# エラー: API key not valid
# 対処: APIキーの制限設定を確認、適切なドメインが許可されているか確認

# エラー: Quota exceeded
# 対処: Google Cloud Console でクォータ制限を確認・増量申請
```

### Cloud Run 設定エラー
```bash
# Secret Manager 権限エラー
gcloud run services add-iam-policy-binding youtube-transcript-secure \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --region=asia-northeast1
```

---

**🔐 このガイドに従うことで、本番環境での安全なAPI運用が可能になります。**