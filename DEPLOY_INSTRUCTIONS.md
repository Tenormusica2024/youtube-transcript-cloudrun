# YouTube Transcript App - Cloud Run デプロイ手順書

## 🚀 準備完了状況
- ✅ APIキー取得済み: `AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw`
- ✅ ローカルテスト完了: Webインターフェース正常動作
- ✅ YouTube API設定完了: ヘルスチェック正常
- ✅ Dockerイメージビルド完了

## 📋 デプロイ手順

### Method 1: Google Cloud Shell (推奨)

1. **Cloud Shell を開く**
   ```
   https://shell.cloud.google.com/
   ```

2. **プロジェクト設定**
   ```bash
   # プロジェクトIDを設定（例: youtube-transcript-123456）
   export PROJECT_ID="your-project-id"
   gcloud config set project $PROJECT_ID
   ```

3. **必要なAPIを有効化**
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

4. **アプリケーションファイルを作成**
   
   Cloud Shell エディタで以下のファイルを作成：

   **app.py:**
   ```
   （app_cloud_run.pyの内容をコピー）
   ```

   **requirements.txt:**
   ```
   Flask==2.3.3
   flask-cors==4.0.0
   google-api-python-client==2.100.0
   google-auth==2.23.0
   google-auth-httplib2==0.1.1
   youtube-transcript-api==0.6.2
   python-dotenv==1.0.0
   gunicorn==21.2.0
   requests==2.31.0
   ```

   **Dockerfile:**
   ```
   （Dockerfileの内容をコピー）
   ```

5. **templatesフォルダとindex.htmlを作成**
   ```bash
   mkdir templates
   # templates/index.html を作成（内容をコピー）
   ```

6. **Cloud Run にデプロイ**
   ```bash
   gcloud run deploy youtube-transcript \
     --source . \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --set-env-vars YOUTUBE_API_KEY=AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw \
     --port 8080 \
     --memory 512Mi \
     --timeout 300
   ```

### Method 2: ローカルからの直接デプロイ

1. **gcloud CLI をインストール**
   ```
   https://cloud.google.com/sdk/docs/install
   ```

2. **認証**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **ローカルからデプロイ**
   ```bash
   cd C:\Users\Tenormusica\youtube_transcript_webapp
   
   gcloud run deploy youtube-transcript \
     --source . \
     --platform managed \
     --region asia-northeast1 \
     --allow-unauthenticated \
     --set-env-vars YOUTUBE_API_KEY=AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw
   ```

## ✅ デプロイ成功後の確認

1. **Service URL を取得**
   ```bash
   gcloud run services describe youtube-transcript \
     --platform managed \
     --region asia-northeast1 \
     --format 'value(status.url)'
   ```

2. **ヘルスチェック**
   ```bash
   curl https://YOUR_SERVICE_URL/health
   ```
   
   期待される結果:
   ```json
   {"status":"healthy","timestamp":"...","youtube_api":"configured"}
   ```

3. **Webインターフェース確認**
   ブラウザで `https://YOUR_SERVICE_URL` にアクセス

4. **API テスト**
   ```bash
   curl -X POST https://YOUR_SERVICE_URL/extract \
     -H 'Content-Type: application/json' \
     -d '{
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "lang": "en",
       "format": "txt"
     }'
   ```

## 🔧 トラブルシューティング

### デプロイエラーの場合
```bash
# ログを確認
gcloud run services logs read youtube-transcript \
  --region asia-northeast1 --limit=50
```

### API制限エラーの場合
- YouTube Data API の使用量をCloud Consoleで確認
- APIキーの制限設定を確認

### 権限エラーの場合
```bash
# 必要な権限を確認
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"
```

## 📊 期待される結果

デプロイが成功すると：
- ✅ Public URL でWebアプリにアクセス可能
- ✅ YouTube動画の字幕抽出が動作
- ✅ 複数言語・フォーマット対応
- ✅ レスポンシブなWebインターフェース

## 💰 料金について

- Cloud Run: 最初の200万リクエスト/月は無料
- YouTube Data API: 1日10,000クエリまで無料
- 通常の利用では月額数円程度

---

**🎉 すべての準備が完了しています！上記手順でCloud Runにデプロイしてください。**