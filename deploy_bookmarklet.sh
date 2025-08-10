#!/bin/bash

# YouTube Transcript Extractor - Bookmarklet版デプロイスクリプト
# セキュリティ強化＋簡単デプロイ

set -e  # エラー時に停止

echo "🎬 YouTube Transcript Extractor (Bookmarklet版) デプロイ開始"
echo "="*60

# 設定確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ Google Cloud プロジェクトが設定されていません"
    echo "gcloud config set project YOUR_PROJECT_ID を実行してください"
    exit 1
fi

echo "📋 設定情報:"
echo "  プロジェクトID: $PROJECT_ID"
echo "  リージョン: asia-northeast1"
echo "  サービス名: youtube-transcript-bookmarklet"

# 必要なAPIを有効化
echo ""
echo "🔧 必要なAPIを有効化中..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Docker イメージビルド
echo ""
echo "🐳 Dockerイメージをビルド中..."
IMAGE_NAME="gcr.io/$PROJECT_ID/youtube-transcript-bookmarklet"

gcloud builds submit --tag "$IMAGE_NAME" --file Dockerfile.bookmarklet .

# Cloud Runにデプロイ
echo ""
echo "🚀 Cloud Runにデプロイ中..."

gcloud run deploy youtube-transcript-bookmarklet \
    --image "$IMAGE_NAME" \
    --platform managed \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60s \
    --max-instances 10 \
    --min-instances 0 \
    --concurrency 100 \
    --set-env-vars "MAX_TRANSCRIPT_LENGTH=50000,SUMMARY_SENTENCES=4,RATE_LIMIT_PER_10MIN=20"

# デプロイ結果を取得
echo ""
echo "✅ デプロイ完了！"
echo ""

SERVICE_URL=$(gcloud run services describe youtube-transcript-bookmarklet \
    --platform managed \
    --region asia-northeast1 \
    --format 'value(status.url)')

echo "🌐 サービスURL: $SERVICE_URL"
echo ""

# ヘルスチェック
echo "🔍 ヘルスチェック実行中..."
if curl -s "$SERVICE_URL/healthz" > /dev/null; then
    echo "✅ ヘルスチェック成功"
else
    echo "⚠️ ヘルスチェック失敗（デプロイ直後のため、少し待ってから再試行してください）"
fi

# 使用方法を表示
echo ""
echo "📋 次のステップ:"
echo ""
echo "1. ブラウザで以下のURLにアクセス:"
echo "   $SERVICE_URL"
echo ""
echo "2. ページでAPI URLを設定（上記URLを入力）"
echo ""
echo "3. ブックマークレットを生成してドラッグ&ドロップ"
echo ""
echo "4. YouTubeでテスト:"
echo "   https://www.youtube.com/watch?v=dQw4w9WgXcQ"
echo ""

# オプション設定について
echo "⚙️ オプション設定（必要に応じて）:"
echo ""
echo "Gemini AI要約を有効にする場合:"
echo "gcloud run services update youtube-transcript-bookmarklet \\"
echo "  --region asia-northeast1 \\"
echo "  --set-env-vars GEMINI_API_KEY=your_gemini_api_key_here"
echo ""

# セキュリティ設定
echo "🔒 セキュリティ設定完了:"
echo "  ✅ CORS: YouTube.comからのみ許可"
echo "  ✅ レート制限: IP毎に10分で20リクエスト"
echo "  ✅ 非rootユーザー実行"
echo "  ✅ セキュリティヘッダー設定"
echo ""

echo "🎉 デプロイ完了！ポートフォリオに追加できます。"
echo ""
echo "📊 ログ確認（デバッグ用）:"
echo "gcloud logs read 'resource.type=cloud_run_revision resource.labels.service_name=youtube-transcript-bookmarklet' --limit=20"

exit 0