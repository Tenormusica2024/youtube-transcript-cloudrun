# Cloud Deployment Setup Guide

## YouTube Transcript App - Cloud Run Deployment

### GitHub Repository
- URL: https://github.com/Tenormusica2024/youtube-transcript-cloudrun
- Status: ✅ Code pushed successfully

### API Keys
- **YouTube Data API v3**: `[REDACTED_FOR_SECURITY]`
- **Google Gemini API**: `[REDACTED_FOR_SECURITY]`

## Cloud Build Setup

### 1. Enable Cloud Build API
- Navigate to: Google Cloud Console > APIs & Services > Library
- Search for "Cloud Build API" and enable it

### 2. Create Build Trigger
- Navigate to: Cloud Build > Triggers
- Click "Create Trigger"

**Trigger Configuration:**
- **Name**: `youtube-transcript-deploy`
- **Event**: Push to a branch
- **Source**: 
  - Repository: `github_Tenormusica2024_youtube-transcript-cloudrun`
  - Branch**: `^main$` (or `^master$`)
- **Configuration**:
  - Type: Cloud Build configuration file (yaml or json)
  - Location: Repository
  - Cloud Build configuration file location: `/cloudbuild.yaml`

### 3. Environment Variables (Substitution Variables)
Add these substitution variables in the trigger:
```
_YOUTUBE_API_KEY = [REDACTED_FOR_SECURITY]
_GEMINI_API_KEY = [REDACTED_FOR_SECURITY]
```

## Cloud Run Setup

### 1. Service Configuration
- **Service Name**: `youtube-transcript`
- **Region**: `asia-northeast1`
- **Platform**: Managed
- **Authentication**: Allow unauthenticated invocations

### 2. Environment Variables Setup
Navigate to: Cloud Run > youtube-transcript service > Edit & Deploy New Revision

**Variables & Secrets Tab:**
```
YOUTUBE_API_KEY = [REDACTED_FOR_SECURITY]
GEMINI_API_KEY = [REDACTED_FOR_SECURITY]
```

### 3. Container Settings
- **Port**: 8080
- **Memory**: 512 MiB
- **CPU**: 1000m
- **Request timeout**: 300 seconds
- **Maximum instances**: 10

## Automatic Deployment Flow

1. **Code Push**: Push code to GitHub main branch
2. **Trigger**: Cloud Build trigger automatically starts
3. **Build**: Docker image is built using Dockerfile
4. **Push**: Image pushed to Google Container Registry
5. **Deploy**: New Cloud Run revision deployed automatically
6. **Environment Variables**: Passed from Cloud Build configuration

## Verification Steps

### 1. Check Build Status
- Cloud Build > History
- Verify build completes successfully

### 2. Test Deployed Service
- Cloud Run > youtube-transcript service
- Copy service URL
- Test with a YouTube URL

### 3. Check Logs
- Cloud Run > youtube-transcript service > Logs
- Monitor for any errors

## Files in Repository

1. **app.py** - Main Flask application
2. **templates/index.html** - Frontend interface
3. **requirements.txt** - Python dependencies
4. **Dockerfile** - Container configuration
5. **cloudbuild.yaml** - Cloud Build pipeline
6. **.env.template** - Environment variables template

## Security Notes

- API keys are stored as environment variables
- Container runs as non-root user
- Health check endpoint available at `/health`
- CORS enabled for cross-origin requests

## Troubleshooting

### Common Issues:
1. **Build fails**: Check cloudbuild.yaml syntax
2. **Environment variables not set**: Verify in Cloud Run service configuration
3. **API quota exceeded**: Monitor API usage in Cloud Console
4. **Service not responding**: Check container logs and health endpoint

### Debugging Commands:
```bash
# Check service status
gcloud run services describe youtube-transcript --region=asia-northeast1

# View logs
gcloud logs read --service=youtube-transcript

# Test health endpoint
curl https://[SERVICE-URL]/health
```

## Status
- ✅ GitHub repository created and code pushed
- ✅ Docker configuration ready
- ✅ Cloud Build configuration ready
- ⏳ Cloud Build trigger setup (manual step required)
- ⏳ Cloud Run environment variables (manual step required)

## Next Steps
1. Login to Google Cloud Console
2. Set up Cloud Build trigger with GitHub repository
3. Configure Cloud Run environment variables
4. Test automatic deployment by pushing a code change