# AI FM Podcast Application

Japanese AI-powered podcast search and playlist management platform.

## 🚀 Quick Start

### Prerequisites
- Google Cloud Project with billing enabled
- gcloud CLI installed and authenticated

### Deployment
```bash
# Clone and navigate to project
cd AI-FM-Podcast-Project-Complete/source-code/podcast-cloud-app

# Deploy to Cloud Run
gcloud run deploy ai-fm-podcast \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id,STORAGE_BUCKET=your-project-id-podcast-audio
```

## 🎵 Features

- **音楽アップロード**: MP3ファイルのGCSアップロード
- **プレイリスト管理**: Firestoreベースのプレイリスト機能
- **検索機能**: アップロード済み楽曲の検索
- **ユーザー認証**: Firebase Authentication (開発モード対応)
- **レスポンシブUI**: モバイル・デスクトップ対応

## 🛠 Architecture

### Frontend
- Vanilla JavaScript (ES6+)
- Firebase SDK for authentication
- Responsive CSS with dark theme

### Backend
- Flask (Python)
- Google Cloud Storage for audio files
- Cloud Firestore for metadata
- Firebase Admin SDK for auth verification

### Infrastructure
- Google Cloud Run (serverless)
- asia-northeast1 region
- Container-based deployment

## ⚠️ Troubleshooting

### Common Issues

**MP3 Upload 500 Error**
- Check GCS bucket existence and permissions
- Verify project environment variables
- See: `TROUBLESHOOTING.md` → Section 1

**Playlist 500 Error** 
- Enable Firestore API
- Create Firestore database
- See: `TROUBLESHOOTING.md` → Section 2

**Quick Fix Commands**
```bash
# Enable required APIs
gcloud services enable firestore.googleapis.com storage.googleapis.com

# Create resources
gcloud storage buckets create gs://PROJECT_ID-podcast-audio --location=asia-northeast1
gcloud firestore databases create --location=asia-northeast1

# Set permissions
PROJECT_NUMBER=$(gcloud projects describe PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## 📚 Documentation

- `TROUBLESHOOTING.md` - Detailed error resolution guide
- `DEPLOYMENT_CONFIG.md` - Current deployment settings
- `app.py` - Inline comments for critical sections

## 🔧 Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export STORAGE_BUCKET=your-project-id-podcast-audio

# Run locally
python app.py
```

### Testing
```bash
# Health check
curl https://your-service-url

# Error monitoring
gcloud logging read "resource.labels.service_name=ai-fm-podcast AND severity>=ERROR" --limit=5
```

## 📊 Current Status

✅ **Working Features:**
- Music upload to GCS
- Playlist creation and management
- Track deletion
- Visual feedback for playlist selection
- Error handling and logging

🏗️ **Architecture:**
- Cloud Run: `ai-fm-podcast-00004-hpt`
- GCS Bucket: `gen-lang-client-0199980214-podcast-audio`
- Firestore: Native mode, asia-northeast1
- Authentication: Firebase (development mode)

## 🆘 Support

For critical issues:
1. Check `TROUBLESHOOTING.md` for known solutions
2. Review Cloud Run logs for specific errors
3. Verify all required APIs are enabled
4. Ensure regional consistency (asia-northeast1)

---
*Last Updated: 2025-08-28*
*Service URL: https://ai-fm-podcast-pwp5dzitha-an.a.run.app*