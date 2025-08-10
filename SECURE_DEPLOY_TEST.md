# 🔒 セキュア版 Cloud Run デプロイテスト手順

## 🎯 目的
セキュリティ強化されたYouTube Transcriptアプリを安全にCloud Runにデプロイし、動作確認を行う

## ✅ 事前確認チェックリスト

### セキュリティ確認:
- [ ] ハードコードされたAPIキーが完全に除去されていることを確認
- [ ] 新しいYouTube Data API v3キーを取得済み
- [ ] 古いAPIキーを無効化済み

### Google Cloud準備:
- [ ] Google Cloud プロジェクトが選択済み
- [ ] 課金が有効化済み
- [ ] Cloud Run API が有効化済み
- [ ] Secret Manager API が有効化済み（オプション）

## 🚀 デプロイ手順

### Option A: 環境変数方式（推奨・簡単）

```bash
# 1. リポジトリクローン（セキュア版）
git clone https://github.com/Tenormusica2024/youtube-transcript-cloudrun.git
cd youtube-transcript-cloudrun
git checkout security-fix-20250810

# 2. APIキー設定（実際のキーに置換）
export YOUTUBE_API_KEY="YOUR_ACTUAL_API_KEY_HERE"

# 3. 必要なAPIを有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# 4. セキュア版デプロイ
gcloud run deploy youtube-transcript-secure \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars YOUTUBE_API_KEY="$YOUTUBE_API_KEY" \
  --port 8080 \
  --memory 512Mi \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0
```

### Option B: Secret Manager方式（推奨・本番環境）

```bash
# 1. Secret ManagerにAPIキーを保存
gcloud secrets create youtube-api-key \
  --data-file=- << EOF
YOUR_ACTUAL_API_KEY_HERE
EOF

# 2. Cloud Runサービスアカウントに権限付与
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud secrets add-iam-policy-binding youtube-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# 3. Secret Manager連携でデプロイ
gcloud run deploy youtube-transcript-secure \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --timeout 300
```

## 🧪 デプロイ後テスト手順

### 1. サービスURL取得
```bash
SERVICE_URL=$(gcloud run services describe youtube-transcript-secure \
  --platform managed \
  --region asia-northeast1 \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### 2. ヘルスチェック
```bash
curl "$SERVICE_URL/health"
# 期待する出力: {"status": "healthy", "timestamp": "...", "youtube_api": "configured"}
```

### 3. トランスクリプト抽出テスト
```bash
curl -X POST "$SERVICE_URL/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "lang": "en",
    "format": "txt"
  }'
```

### 4. Webインターフェーステスト
```bash
# ブラウザで開く
echo "Web Interface: $SERVICE_URL"
```

## 🔍 セキュリティ検証

### 1. APIキー漏洩チェック
```bash
# デプロイしたソースコードにAPIキーがないことを確認
curl "$SERVICE_URL/health" | grep -i "api"
# "youtube_api": "configured" と表示されればOK（キー自体は表示されない）
```

### 2. ログ確認
```bash
gcloud logs read \
  "resource.type=cloud_run_revision resource.labels.service_name=youtube-transcript-secure" \
  --limit=10
```

### 3. 環境変数確認
```bash
gcloud run services describe youtube-transcript-secure \
  --platform managed \
  --region asia-northeast1 \
  --format="export" | grep -i "youtube_api"
# 環境変数は設定されているがキー値は表示されないことを確認
```

## ⚡ トラブルシューティング

### デプロイ失敗
```bash
# エラー詳細確認
gcloud run services describe youtube-transcript-secure \
  --region asia-northeast1 \
  --format="export"

# ビルドログ確認
gcloud logging read "resource.type=build" --limit=20
```

### APIエラー
```bash
# API有効化状況確認
gcloud services list --enabled | grep -E "(run|cloudbuild)"

# 権限確認
gcloud auth list
gcloud config get-value project
```

### トランスクリプト取得失敗
```bash
# APIキー設定確認（値は表示されない）
gcloud run services describe youtube-transcript-secure \
  --region asia-northeast1 \
  --format="get(spec.template.spec.template.spec.containers[0].env)"
```

## 📊 パフォーマンステスト

### 負荷テスト（オプション）
```bash
# 複数リクエスト同時実行
for i in {1..5}; do
  curl -X POST "$SERVICE_URL/extract" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw", "lang": "en", "format": "txt"}' &
done
wait
```

## ✅ 成功判定基準

- [ ] デプロイが成功（エラーなし）
- [ ] ヘルスチェックが200 OKを返す
- [ ] トランスクリプト抽出が正常動作
- [ ] WebUIが表示される
- [ ] APIキーが環境変数から取得される
- [ ] ログにAPIキーが含まれていない
- [ ] レスポンス時間が30秒以内

## 🎉 完了後の作業

1. **Production URL記録**: デプロイ成功したURLを記録
2. **モニタリング設定**: Cloud Monitoringでアラート設定
3. **カスタムドメイン**: 必要に応じてカスタムドメイン設定
4. **バックアップ**: 設定のバックアップ

---

**🔒 このセキュア版は本番環境での使用に適しています。**