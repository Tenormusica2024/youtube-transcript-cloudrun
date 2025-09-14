#!/bin/bash

# Cloud Runデプロイスクリプト

# プロジェクト設定
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}
SERVICE_NAME=${SERVICE_NAME:-podcast-app}
STORAGE_BUCKET=${STORAGE_BUCKET:-${PROJECT_ID}-podcast-audio}

echo "🚀 Deploying Podcast App to Cloud Run"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"

# 必要なAPIを有効化
echo "📡 Enabling APIs..."
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  firestore.googleapis.com \
  firebase.googleapis.com

# Cloud Storageバケット作成
echo "🪣 Creating Storage bucket..."
if ! gsutil ls gs://$STORAGE_BUCKET > /dev/null 2>&1; then
    gsutil mb -l $REGION gs://$STORAGE_BUCKET
    # プライベートアクセス設定
    gsutil uniformbucketlevelaccess set on gs://$STORAGE_BUCKET
    gsutil iam ch allUsers:legacyObjectReader gs://$STORAGE_BUCKET
    echo "✅ Storage bucket created: gs://$STORAGE_BUCKET"
else
    echo "✅ Storage bucket already exists: gs://$STORAGE_BUCKET"
fi

# CORS設定
echo "🌐 Setting up CORS for Storage bucket..."
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type", "Content-Length", "ETag"],
    "maxAgeSeconds": 3600
  }
]
EOF
gsutil cors set cors.json gs://$STORAGE_BUCKET
rm cors.json

# Cloud Buildでデプロイ
echo "🔨 Building and deploying..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# Cloud Runサービスをデプロイ
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=$PROJECT_ID,STORAGE_BUCKET=$STORAGE_BUCKET"

# サービスURL取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')

echo "🎉 Deployment complete!"
echo "Service URL: $SERVICE_URL"
echo "Health check: $SERVICE_URL/api/health"

# Firebase設定の手動手順を表示
echo ""
echo "📝 Next steps:"
echo "1. Go to Firebase Console: https://console.firebase.google.com/"
echo "2. Create/Select your project: $PROJECT_ID"
echo "3. Enable Authentication with Email/Password and Google"
echo "4. Enable Firestore Database in production mode"
echo "5. Update allowed domains to include: $(echo $SERVICE_URL | sed 's|https://||')"
echo "6. Copy Firebase config to your frontend"