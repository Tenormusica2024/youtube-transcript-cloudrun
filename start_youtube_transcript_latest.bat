@echo off
REM YouTube Transcript WebApp - Latest Version Startup Script
REM Version: v1.3.12-fixed (2025-08-21)

echo ========================================
echo  YouTube Transcript WebApp Startup
echo  Version: v1.3.12-fixed
echo  Port: 8087
echo  Features: Filler Removal + AI Summary
echo ========================================

cd /d "C:\Users\Tenormusica\youtube_transcript_webapp"

REM Check if server is already running
netstat -an | findstr :8087 >nul
if %errorlevel% == 0 (
    echo [INFO] Server already running on port 8087
    echo [INFO] Access: http://127.0.0.1:8087
    pause
    exit /b 0
)

REM Kill any existing Python processes on port 8087
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8087') do (
    echo [INFO] Stopping existing process %%a
    taskkill /F /PID %%a >nul 2>&1
)

REM Start the production server
echo [START] Launching production server...
echo [INFO] Main script: production_server.py
echo [INFO] Features enabled:
echo   - Filler removal (86.9%% effectiveness)
echo   - Clean text formatting
echo   - Gemini AI summarization
echo   - Multi-language support

python production_server.py

pause