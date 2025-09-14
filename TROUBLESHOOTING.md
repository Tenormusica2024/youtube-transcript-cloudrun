# AI FM Podcast - トラブルシューティングガイド

## 概要
このドキュメントは、AI FM Podcast アプリケーションで発生する主要なエラーと解決方法を記録します。

## 🚨 Critical Errors & Solutions

### 1. MP3アップロード 500エラー

#### 症状
```
Failed to load resource: the server responded with a status of 500
Upload error: Error: Direct upload failed: 500
```

#### 原因と解決方法

**A. GCSバケット不存在エラー**
```bash
# エラーログ例
ERROR: gs://PROJECT_ID-podcast-audio not found: 404
```
**解決手順:**
```bash
gcloud storage buckets create gs://PROJECT_ID-podcast-audio --location=asia-northeast1
```

**B. GCS権限不足エラー**
```bash
# エラーログ例
"493739562075-compute@developer.gserviceaccount.com does not have storage.objects.create access"
```
**解決手順:**
```bash
# 1. プロジェクト番号を取得
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")

# 2. プロジェクトレベル権限付与
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 3. バケットレベル権限付与
gcloud storage buckets add-iam-policy-binding gs://PROJECT_ID-podcast-audio \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 4. 統合バケットレベルアクセス有効化
gcloud storage buckets update gs://PROJECT_ID-podcast-audio --uniform-bucket-level-access
```

**C. 環境変数不整合エラー**
```bash
# 間違ったプロジェクト名がハードコードされている場合
# Cloud Run環境変数を正しく設定
gcloud run services update ai-fm-podcast --region asia-northeast1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=実際のプロジェクトID,STORAGE_BUCKET=実際のプロジェクトID-podcast-audio
```

### 2. プレイリスト機能 500エラー

#### 症状
```javascript
📡 API Request: {method: 'POST', url: '/api/playlists'}
❌ Response error body: {"error":"Failed to create playlist"}
```

#### 原因と解決方法

**A. Firestore API未有効化**
```bash
# エラーログ例
"Cloud Firestore API has not been used in project before or it is disabled"
```
**解決手順:**
```bash
# 1. Firestore API有効化
gcloud services enable firestore.googleapis.com --project=PROJECT_ID

# 2. Firestoreデータベース作成
gcloud firestore databases create --location=asia-northeast1 --project=PROJECT_ID

# 3. Cloud Runサービス再起動（設定反映のため）
gcloud run services update ai-fm-podcast --region asia-northeast1 --no-traffic
```

## 🛠 一般的なデプロイメント手順

### 初回セットアップ
```bash
# 1. 必要なAPIを有効化
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  --project=PROJECT_ID

# 2. Firestoreデータベース作成
gcloud firestore databases create --location=asia-northeast1 --project=PROJECT_ID

# 3. GCSバケット作成
gcloud storage buckets create gs://PROJECT_ID-podcast-audio --location=asia-northeast1

# 4. サービスアカウント権限設定
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# 5. Cloud Runデプロイ
gcloud run deploy ai-fm-podcast \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=PROJECT_ID,STORAGE_BUCKET=PROJECT_ID-podcast-audio
```

### デバッグ用ログ確認
```bash
# 最新エラーログ確認
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-fm-podcast AND severity>=ERROR" \
  --limit=10 \
  --format="value(textPayload)"

# 特定文字列でフィルタ
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-fm-podcast" \
  --limit=20 \
  --format="value(textPayload)" | grep -i "firestore\|storage"
```

## 🔄 リカバリーチェックリスト

### MP3アップロードエラー時
- [ ] プロジェクト名とバケット名の整合性確認
- [ ] GCSバケットの存在確認
- [ ] サービスアカウント権限確認
- [ ] Cloud Run環境変数確認

### プレイリストエラー時
- [ ] Firestore APIの有効化状況確認
- [ ] Firestoreデータベースの存在確認
- [ ] Cloud Runサービスの再起動

## 📍 重要なロケーション設定

### リージョン統一
すべてのリソースを `asia-northeast1` で統一：
- Cloud Run サービス
- GCS バケット
- Firestore データベース

### 命名規則
- プロジェクトID: `gen-lang-client-0199980214`
- バケット名: `{PROJECT_ID}-podcast-audio`
- サービス名: `ai-fm-podcast`

## 🚀 予防策

### コード内での事前チェック
```python
# app.py内で実装済み
# 1. GCSバケット存在確認
# 2. Firestore接続確認
# 3. 詳細エラーログ出力
```

### 定期的な健全性チェック
```bash
# サービス稼働確認
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://ai-fm-podcast-pwp5dzitha-an.a.run.app/

# ログ監視（エラー発生時）
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=ai-fm-podcast AND severity>=ERROR" \
  --limit=5 \
  --format="value(textPayload,timestamp)"
```

## 📞 エスカレーション

### 重大度レベル1 (即座対応)
- MP3アップロード完全停止
- 全プレイリスト機能停止

### 重大度レベル2 (24時間以内)
- 間欠的なアップロード失敗
- 特定機能の部分的障害

---
*最終更新: 2025-08-28*
*次回更新予定: 新しいエラーパターン発見時*