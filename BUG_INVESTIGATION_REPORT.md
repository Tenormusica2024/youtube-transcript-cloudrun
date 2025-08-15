# Bug Investigation Report: 401 UNAUTHORIZED Error

## Issue Summary

**Date**: 2025-08-15  
**Reporter**: User  
**Severity**: High (Service Unusable)  
**Status**: ✅ RESOLVED

### Problem Description
The YouTube Transcript Extractor local service running on port 8765 was returning `401 UNAUTHORIZED` errors when accessing the `/extract` endpoint, making the tool completely unusable.

## Root Cause Analysis

### 🔍 Investigation Process

1. **Service Status Check**: Confirmed service was running on port 8765
2. **Authentication Flow Analysis**: Identified missing authentication token in environment configuration
3. **Code Review**: Examined `@require_auth` decorator implementation
4. **Environment Variable Audit**: Found missing `TRANSCRIPT_API_TOKEN` in `.env` file

### 🚨 Root Cause
**Missing Environment Variable**: The `/extract` endpoint requires authentication via the `@require_auth` decorator, which expects a `TRANSCRIPT_API_TOKEN` environment variable. This variable was not defined in the `.env` file, causing `get_transcript_api_token()` to fail and reject all requests.

### 📍 Affected Code
- **File**: `app.py:80-94` - `get_transcript_api_token()` function
- **File**: `app.py:96-141` - `@require_auth` decorator
- **File**: `app.py:500-501` - `/extract` endpoint with `@require_auth`
- **File**: `.env` - Missing `TRANSCRIPT_API_TOKEN` variable

## Solution Implementation

### ✅ Fix Applied

1. **Added Missing Environment Variable**:
   ```bash
   # Added to .env file
   TRANSCRIPT_API_TOKEN=hybrid-yt-token-2024
   ```

2. **Enhanced Debugging**:
   - Added comprehensive logging to the authentication flow
   - Improved error messages for troubleshooting
   - Added auth header parsing validation

### 🧪 Verification

**Test Case 1: English Text**
```bash
curl -X POST "http://localhost:8765/extract" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer hybrid-yt-token-2024" \
  -d '{"transcript_text": "This is a test transcript text.", "lang": "en", "format": "txt"}'
```
**Result**: ✅ SUCCESS - Returns formatted transcript with Gemini AI summary

**Test Case 2: Japanese Text**
```bash
curl -X POST "http://localhost:8765/extract" \
  -H "Content-Type: application/json; charset=utf-8" \
  -H "Authorization: Bearer hybrid-yt-token-2024" \
  -d @test_request.json
```
**Result**: ✅ SUCCESS - Properly handles UTF-8 Japanese text with formatting and summarization

## Authentication Flow (Fixed)

```
1. Client Request → Authorization: Bearer hybrid-yt-token-2024
2. @require_auth decorator validates:
   ├── Header exists ✓
   ├── Format "Bearer <token>" ✓  
   ├── Token matches TRANSCRIPT_API_TOKEN ✓
   └── Proceeds to endpoint ✓
3. Service processes request successfully ✓
```

## Files Modified

1. **`.env`** - Added `TRANSCRIPT_API_TOKEN=hybrid-yt-token-2024`
2. **`app.py`** - Enhanced authentication logging and error handling
3. **`debug_auth.py`** - Created debugging utility (temporary)
4. **`test_request.json`** - Created UTF-8 test case (temporary)

## Prevention Measures

### 🛡️ Recommendations

1. **Environment Variable Validation**: Add startup checks to ensure all required environment variables are present
2. **Documentation Update**: Update README with complete environment variable requirements
3. **Health Check Enhancement**: Include authentication token validation in `/health` endpoint
4. **Testing Suite**: Add integration tests for authentication flow

### 📝 Environment Variable Checklist

Required variables for full functionality:
- ✅ `YOUTUBE_API_KEY` - YouTube Data API access
- ✅ `GEMINI_API_KEY` - AI text formatting and summarization  
- ✅ `TRANSCRIPT_API_TOKEN` - **[FIXED]** API endpoint authentication
- ✅ `API_AUTH_TOKEN` - Legacy token (for compatibility)

## Impact Assessment

- **Downtime**: Service was completely unusable for `/extract` endpoint
- **User Experience**: All transcript extraction requests failed with 401 errors
- **Data Loss**: None (authentication issue, no data corruption)
- **Security**: No security vulnerabilities identified

## Resolution Confirmation

- **Service Status**: ✅ Running (http://localhost:8765)
- **Authentication**: ✅ Working with Bearer token
- **Text Processing**: ✅ English and Japanese support
- **Gemini AI Integration**: ✅ Formatting and summarization working
- **UTF-8 Encoding**: ✅ Properly handled

## Next Steps

1. Monitor service stability over 24-48 hours
2. Consider implementing automated health checks
3. Update documentation with this investigation
4. Add the missing token to deployment documentation

---

**Investigation Completed**: 2025-08-15 22:14 JST  
**Service Status**: ✅ OPERATIONAL  
**Issue Status**: 🔒 CLOSED - RESOLVED