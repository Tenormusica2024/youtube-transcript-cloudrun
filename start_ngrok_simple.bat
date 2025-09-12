@echo off
echo ============================================================
echo YouTube字幕抽出ツール - ngrok固定URL版 v1.5.1-clean
echo DEMO DATA REMOVED - Production Only
echo ============================================================

cd /d "C:\Users\Tenormusica\youtube_transcript_webapp"

echo Starting ngrok tunnel with fixed domain...
start "ngrok" "C:\Users\Tenormusica\ngrok.exe" http 8085 --hostname=yt-transcript.ngrok.io

echo Waiting for ngrok to initialize...
timeout /t 5

echo ============================================================
echo ✅ SYSTEM READY!
echo 🌐 Public URL: https://yt-transcript.ngrok.io  
echo 🏠 Local URL: http://127.0.0.1:8085
echo ============================================================
echo Flask app is already running on port 8085
echo Press any key to stop ngrok...
pause
taskkill /im ngrok.exe /f