@echo off
REM Production Start Script with SSL (Windows)
REM YouTube Transcript Webapp - App Store Ready

set FLASK_ENV=production
set SSL_KEYFILE=ssl/private.key
set SSL_CERTFILE=ssl/certificate.crt

echo [PRODUCTION] Starting YouTube Transcript App with SSL
echo [HTTPS] Enabled on port 8085
echo [APPSTORE] Compliance mode active

REM Install production requirements if needed
if not exist venv (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements_production.txt
) else (
    call venv\Scripts\activate
)

REM Start with Gunicorn or Flask
if exist gunicorn.conf.py (
    echo [GUNICORN] Starting with production configuration
    python -m gunicorn -c gunicorn.conf.py app_mobile:app
) else (
    echo [FLASK] Starting with built-in server
    python app_mobile.py
)

pause
