#!/bin/bash
# Production Start Script with SSL
# YouTube Transcript Webapp - App Store Ready

export FLASK_ENV=production
export SSL_KEYFILE=ssl/private.key
export SSL_CERTFILE=ssl/certificate.crt

echo "[PRODUCTION] Starting YouTube Transcript App with SSL"
echo "[HTTPS] Enabled on port 8085"
echo "[APPSTORE] Compliance mode active"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements_production.txt
else
    source venv/bin/activate
fi

# Start with Gunicorn or Flask
if [ -f "gunicorn.conf.py" ]; then
    echo "[GUNICORN] Starting with production configuration"
    gunicorn -c gunicorn.conf.py app_mobile:app
else
    echo "[FLASK] Starting with built-in server"
    python app_mobile.py
fi
