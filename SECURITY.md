# Security Policy

## 🔒 Security Overview

This YouTube Transcript Extractor application implements security best practices to protect against common vulnerabilities and ensure safe deployment.

## ⚡ Quick Security Check

**Before deployment, verify:**
- [ ] No hardcoded API keys in code
- [ ] Environment variables used for secrets
- [ ] Latest security patches applied
- [ ] Non-root container execution
- [ ] Input validation implemented

## 🔍 Security Features

### 🔐 API Key Protection
- **Environment Variables**: Secrets stored in environment variables, not code
- **Google Cloud Secret Manager**: Support for centralized secret management
- **No Hardcoding**: Zero hardcoded credentials in source code
- **Key Rotation**: Easy API key rotation without code changes

### 🛡️ Application Security
- **Input Validation**: All user inputs validated and sanitized
- **XSS Prevention**: Output encoding and Content Security Policy
- **HTTPS Enforcement**: All communication over encrypted channels
- **Error Handling**: Prevents information disclosure through error messages

### 🐳 Container Security
- **Non-root Execution**: Application runs as non-privileged user (appuser:1000)
- **Minimal Base Image**: Python slim image reduces attack surface  
- **Security Updates**: Regular base image updates
- **Read-only Filesystem**: Application files mounted read-only where possible

### 🚀 Cloud Run Security
- **IAM Integration**: Google Cloud IAM for access control
- **Private Networking**: Optional VPC connector support
- **Service Account**: Minimal permissions service account
- **Automatic TLS**: HTTPS termination by Google Cloud

## 🚨 Vulnerability Reporting

### Reporting Security Issues
If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** create a public GitHub issue
2. **Do NOT** disclose the vulnerability publicly
3. **Email**: Send details to the repository owner
4. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact assessment
   - Suggested fix (if available)

### Response Timeline
- **Initial Response**: Within 24 hours
- **Assessment**: Within 72 hours  
- **Fix Timeline**: Based on severity (Critical: 24-48h, High: 1 week, Medium: 2 weeks)
- **Disclosure**: Coordinated disclosure after fix deployment

## 🔧 Security Configuration

### Environment Variables
```bash
# Required for title retrieval (optional)
YOUTUBE_API_KEY=your_api_key_here

# Cloud Run automatically provides
PORT=8080
K_SERVICE=youtube-transcript-secure
GOOGLE_CLOUD_PROJECT=your_project_id
```

### Google Cloud Setup
```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create secret for API key
gcloud secrets create youtube-api-key --data-file=api_key.txt

# Grant access to Cloud Run service account
PROJECT_ID=$(gcloud config get-value project)
gcloud secrets add-iam-policy-binding youtube-api-key \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## 🔍 Security Testing

### Automated Security Scans
Our CI/CD pipeline includes:
- **Bandit**: Python security linting
- **Safety**: Dependency vulnerability scanning  
- **TruffleHog**: Secret scanning
- **Container Scanning**: Docker image vulnerability assessment

### Manual Security Testing
```bash
# Check for hardcoded secrets
grep -r "AIzaSy[A-Za-z0-9_-]\{33\}" . --exclude-dir=.git

# Vulnerability scan
bandit -r . -x ./tests/
safety check

# Container security scan
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image youtube-transcript-secure:latest
```

## 📋 Security Checklist

### Pre-deployment
- [ ] Security scan passed (bandit, safety)
- [ ] No hardcoded credentials
- [ ] Dependencies updated to latest secure versions
- [ ] Container runs as non-root user
- [ ] Environment variables configured
- [ ] Input validation implemented
- [ ] Error handling prevents information disclosure

### Post-deployment  
- [ ] HTTPS endpoint accessible
- [ ] Health check responds correctly
- [ ] API functionality works without exposing errors
- [ ] Logs don't contain sensitive information
- [ ] Resource limits configured properly
- [ ] Access controls verified

## 🚫 Known Limitations

### Current Security Limitations
- **Rate Limiting**: Basic rate limiting (Cloud Run level only)
- **Authentication**: Currently allows anonymous access
- **Input Size**: Limited input validation on URL length
- **Error Messages**: May leak some system information in error responses

### Future Security Improvements
- [ ] Implement rate limiting per IP
- [ ] Add API key authentication for high-volume usage
- [ ] Enhanced input validation and sanitization
- [ ] Web Application Firewall (WAF) integration
- [ ] Advanced threat detection and monitoring

## 📚 Security Resources

### Documentation
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Container Security Best Practices](https://cloud.google.com/architecture/best-practices-for-operating-containers)

### Security Tools
- [Bandit](https://bandit.readthedocs.io/): Python security linting
- [Safety](https://pyup.io/safety/): Python dependency scanning
- [TruffleHog](https://trufflesecurity.com/trufflehog): Secret scanning
- [Trivy](https://trivy.dev/): Container vulnerability scanning

## 🔄 Security Updates

This document is regularly updated to reflect current security practices and threat landscape changes. Last updated: August 2025.

**For the latest security information, check the repository's security advisories and release notes.**