@echo off
echo ====================================
echo YouTube Transcript App Local Test
echo ====================================

echo.
echo 1. Setting up environment...
cd /d "C:\Users\Tenormusica\youtube_secure_updated"

echo.
echo 2. Running security tests...
python quick_test.py

echo.
echo 3. Testing transcript extraction without API key...
python -c "from youtube_transcript_api import YouTubeTranscriptApi; api = YouTubeTranscriptApi(); transcript = api.fetch('dQw4w9WgXcQ', languages=['en']).to_raw_data(); print(f'SUCCESS: Extracted {len(transcript)} transcript segments')"

echo.
echo ====================================
echo Local Test Complete!
echo ====================================
echo.
echo To run the full app with API key:
echo 1. Set environment variable: set YOUTUBE_API_KEY=your_key_here  
echo 2. Run: python app.py
echo 3. Open: http://localhost:8080
echo.

pause