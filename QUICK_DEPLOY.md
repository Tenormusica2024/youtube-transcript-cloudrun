# 🔒 Secure Cloud Run Deployment

> ⚠️ **Security Enhanced**: This version implements proper API key management and removes hardcoded secrets.

## 🚨 Important Security Notice

**This deployment method follows security best practices:**
- ❌ No hardcoded API keys
- ✅ Environment variable based configuration  
- ✅ Google Cloud Secret Manager support
- ✅ Secure container execution

## 🔐 Prerequisites

### 1. Get YouTube Data API v3 Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Enable YouTube Data API v3
4. Create an API key with appropriate restrictions
5. **Keep your API key secure** - never commit it to code

## 🚀 Secure Deployment Steps

### Option A: Environment Variable Method

```bash
# Set your API key (replace YOUR_API_KEY with actual key)
export YOUTUBE_API_KEY="YOUR_API_KEY_HERE"

# Open Google Cloud Shell
# Visit: https://shell.cloud.google.com/

# Clone the repository
git clone https://github.com/Tenormusica2024/youtube-transcript-cloudrun.git
cd youtube-transcript-cloudrun

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Deploy to Cloud Run with secure configuration
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

# Get the service URL
gcloud run services describe youtube-transcript-secure \
  --platform managed \
  --region asia-northeast1 \
  --format 'value(status.url)'
```

### Option B: Google Cloud Secret Manager (Recommended)

```bash
# Store API key in Secret Manager
gcloud secrets create youtube-api-key --data-file=- << EOF
YOUR_API_KEY_HERE
EOF

# Grant access to Cloud Run service account
PROJECT_ID=$(gcloud config get-value project)
SERVICE_ACCOUNT="${PROJECT_ID}@appspot.gserviceaccount.com"

gcloud secrets add-iam-policy-binding youtube-api-key \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

# Deploy without exposing API key in environment variables
gcloud run deploy youtube-transcript-secure \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --timeout 300
```

## ✅ Post-Deployment Verification

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe youtube-transcript-secure \
  --platform managed \
  --region asia-northeast1 \
  --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"

# Health check
curl "$SERVICE_URL/health"

# Test transcript extraction
curl -X POST "$SERVICE_URL/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "lang": "en",
    "format": "txt"
  }'
```

## 🔒 Security Features

This deployment includes:

- ✅ **No hardcoded secrets**: API keys managed via environment variables or Secret Manager
- ✅ **Input validation**: All user inputs are validated and sanitized
- ✅ **Security headers**: HTTPS, XSS protection, content security policy
- ✅ **Non-root container**: Application runs as non-privileged user
- ✅ **Error handling**: Prevents information disclosure through error messages
- ✅ **Rate limiting**: Basic protection against abuse (Cloud Run level)

## 🚨 Security Checklist

Before deployment:
- [ ] API key is not hardcoded in any files
- [ ] API key has appropriate restrictions (YouTube Data API v3 only)
- [ ] Project has billing account configured
- [ ] Cloud Run API is enabled
- [ ] Secret Manager API is enabled (if using Option B)

After deployment:
- [ ] Health check responds correctly
- [ ] Transcript extraction works
- [ ] No sensitive information in logs
- [ ] HTTPS endpoint is accessible
- [ ] Error responses don't leak system information

## 🛡️ Monitoring and Maintenance

### View Logs
```bash
gcloud logs read "resource.type=cloud_run_revision resource.labels.service_name=youtube-transcript-secure" --limit=50
```

### Update API Key
```bash
# For environment variable method
gcloud run services update youtube-transcript-secure \
  --set-env-vars YOUTUBE_API_KEY="NEW_API_KEY"

# For Secret Manager method
gcloud secrets versions add youtube-api-key --data-file=- << EOF
NEW_API_KEY
EOF
```

### Scale Configuration
```bash
gcloud run services update youtube-transcript-secure \
  --max-instances=20 \
  --min-instances=1 \
  --concurrency=100
```

## ⚠️ Important Notes

1. **API Costs**: YouTube Data API v3 has quotas and potential costs
2. **Rate Limits**: Implement additional rate limiting for high-traffic scenarios
3. **Monitoring**: Set up Cloud Monitoring for production usage
4. **Backup**: Keep backups of your API keys and configuration

## 🆘 Troubleshooting

### Common Issues

**Transcript not found**: 
- Video may not have captions available
- Try different language codes

**API errors**:
- Check API key restrictions
- Verify YouTube Data API v3 is enabled
- Check quota usage in Google Cloud Console

**Deployment fails**:
- Ensure billing is enabled
- Check IAM permissions
- Verify region availability

### Getting Help

1. Check Cloud Run logs: `gcloud logs read ...`
2. Verify API key: Test with YouTube API directly
3. Review security settings: Ensure proper IAM roles

---

**🔒 Security-first deployment for production use!**