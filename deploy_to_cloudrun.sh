#!/bin/bash

# YouTube Transcript App - Cloud Run Deployment Script
echo "=================================================="
echo "YouTube Transcript App - Cloud Run Deployment"
echo "=================================================="

# Set your project ID here
PROJECT_ID="your-project-id"
SERVICE_NAME="youtube-transcript"
REGION="asia-northeast1"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud SDK (gcloud) is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1 > /dev/null; then
    echo "❌ Not authenticated with Google Cloud"
    echo "Please run: gcloud auth login"
    exit 1
fi

# Set the project
echo "📋 Setting project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Build and deploy using Cloud Build
echo "🚀 Building and deploying to Cloud Run..."
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_YOUTUBE_API_KEY="$YOUTUBE_API_KEY"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --format 'value(status.url)')

echo "=================================================="
echo "✅ Deployment completed successfully!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📋 Service Name: $SERVICE_NAME"
echo "📍 Region: $REGION"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Set your YouTube Data API key:"
echo "   gcloud run services update $SERVICE_NAME \\"
echo "     --set-env-vars YOUTUBE_API_KEY=YOUR_API_KEY \\"
echo "     --region $REGION"
echo ""
echo "2. Test the service:"
echo "   curl -X POST $SERVICE_URL/extract \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"url\":\"https://www.youtube.com/watch?v=dQw4w9WgXcQ\",\"lang\":\"en\",\"format\":\"txt\"}'"
echo ""
echo "3. Access the web interface: $SERVICE_URL"
echo "=================================================="