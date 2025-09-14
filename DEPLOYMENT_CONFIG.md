# AI FM Podcast - デプロイメント設定

## 🔧 現在の設定 (2025-08-28)

### プロジェクト情報
```
プロジェクトID: gen-lang-client-0199980214
プロジェクト番号: 493739562075
リージョン: asia-northeast1
```

### Cloud Run設定
```
サービス名: ai-fm-podcast
URL: https://ai-fm-podcast-pwp5dzitha-an.a.run.app
現在のリビジョン: ai-fm-podcast-00004-hpt
メモリ: 512Mi
CPU: 1000m
最大インスタンス: 20
タイムアウト: 300s
```

### 環境変数
```bash
GOOGLE_CLOUD_PROJECT=gen-lang-client-0199980214
STORAGE_BUCKET=gen-lang-client-0199980214-podcast-audio
```

### GCSバケット
```
バケット名: gs://gen-lang-client-0199980214-podcast-audio
ロケーション: asia-northeast1
アクセス制御: Uniform bucket-level access
作成日: 2025-08-28
```

### Firestore
```
データベース名: (default)
ロケーション: asia-northeast1
タイプ: FIRESTORE_NATIVE
作成日: 2025-08-28T11:41:41.141511Z
```

### サービスアカウント
```
アカウント: 493739562075-compute@developer.gserviceaccount.com
権限:
  - roles/storage.objectAdmin (プロジェクトレベル)
  - roles/storage.objectAdmin (バケットレベル)
  - roles/editor (プロジェクトレベル)
  - roles/run.admin (プロジェクトレベル)
```

## 📋 デプロイメント履歴

### 2025-08-28 セッション
1. **ai-fm-podcast-00001-xmq**: CSS変数修正
2. **ai-fm-podcast-00002-rph**: textContentエラー修正
3. **ai-fm-podcast-00003-f7v**: GCS権限設定後
4. **ai-fm-podcast-00004-hpt**: 環境変数修正 (現在)

## 🚀 標準デプロイコマンド

### 通常デプロイ
```bash
cd C:\Users\Tenormusica\AI-FM-Podcast-Project-Complete\source-code\podcast-cloud-app
gcloud run deploy ai-fm-podcast \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --quiet
```

### 環境変数付きデプロイ
```bash
gcloud run deploy ai-fm-podcast \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=gen-lang-client-0199980214,STORAGE_BUCKET=gen-lang-client-0199980214-podcast-audio \
  --quiet
```

### 設定のみ更新（リビルドなし）
```bash
gcloud run services update ai-fm-podcast \
  --region asia-northeast1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=gen-lang-client-0199980214,STORAGE_BUCKET=gen-lang-client-0199980214-podcast-audio
```

## 🔍 確認コマンド

### サービス状態確認
```bash
gcloud run services describe ai-fm-podcast --region asia-northeast1
```

### 環境変数確認
```bash
gcloud run services describe ai-fm-podcast \
  --region asia-northeast1 \
  --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

### ログ確認
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-fm-podcast" \
  --limit=10 \
  --format="value(textPayload,timestamp)"
```

### バケット確認
```bash
gcloud storage buckets describe gs://gen-lang-client-0199980214-podcast-audio
```

### Firestore確認
```bash
gcloud firestore databases describe --database="(default)" --project=gen-lang-client-0199980214
```

## 📊 監視設定

### ヘルスチェック
```bash
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://ai-fm-podcast-pwp5dzitha-an.a.run.app/
```

### エラー監視
```bash
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-fm-podcast AND severity>=ERROR" \
  --limit=5 \
  --format="table(timestamp,textPayload)"
```

## 🔐 セキュリティ設定

### IAM権限最小限
- Cloud Storage: objectAdmin のみ
- Firestore: データベース利用者
- Cloud Run: サービス実行

### ネットワーク
- HTTPS強制
- CORS設定: 全オリジン許可（開発用）
- CSP設定: app.py内で定義

---
*設定管理者: Tenormusica*
*最終更新: 2025-08-28T11:41:41Z*