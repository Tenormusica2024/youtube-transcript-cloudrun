#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Transcript App - Fixed Server Startup (Simple Version)
"""

import os
import sys

from dotenv import load_dotenv

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"

# 環境変数を先に設定
load_dotenv()

# ポートを8085に強制設定
os.environ["PORT"] = "8085"

# ライブラリインポートチェック
try:
    import flask
    import google.generativeai as genai
    import googleapiclient.discovery
    from flask_cors import CORS
    from youtube_transcript_api import YouTubeTranscriptApi

    print("Required libraries are available")
except ImportError as e:
    print(f"Library import error: {e}")
    sys.exit(1)

# APIキー確認
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

print("YouTube Transcript App - Starting Fixed Server")
print("=" * 50)
print(f"Server starting on: http://localhost:8085")
print(f"YouTube API: {'OK' if youtube_api_key else 'NOT FOUND'}")
print(f"Gemini API: {'OK' if gemini_api_key else 'NOT FOUND'}")
print("=" * 50)

# 元のアプリを起動
try:
    from app import app

    print("Original app loaded successfully")
    app.run(host="127.0.0.1", port=8085, debug=False, use_reloader=False)

except Exception as e:
    print(f"Original app startup error: {e}")
    print("Starting fallback server...")

    # フォールバック
    from flask import Flask, jsonify, render_template

    fallback_app = Flask(__name__)
    CORS(fallback_app)

    @fallback_app.route("/")
    def index():
        return """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript App - Recovery Mode</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
        }
        h1 { text-align: center; }
        .status { 
            background: #f39c12; 
            color: white; 
            padding: 15px; 
            border-radius: 8px; 
            margin: 20px 0;
            text-align: center;
        }
        .info { 
            background: rgba(255,255,255,0.2); 
            padding: 15px; 
            border-radius: 8px; 
            margin: 10px 0; 
        }
        a { color: #ffd700; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Transcript App</h1>
        <div class="status">Recovery Mode - Basic Function Available</div>
        
        <div class="info">
            <strong>Status:</strong><br>
            • Server: Running on port 8085<br>
            • Mode: Fallback recovery mode<br>
            • Basic functions: Available
        </div>
        
        <div class="info">
            <strong>Available Endpoints:</strong><br>
            • <a href="/health">Health Check</a><br>
            • <a href="/info">System Info</a><br>
        </div>
        
        <p style="text-align: center; margin-top: 30px;">
            Generated with Claude Code
        </p>
    </div>
</body>
</html>"""

    @fallback_app.route("/health")
    def health():
        return jsonify(
            {
                "status": "recovery_mode",
                "message": "YouTube Transcript App running in recovery mode",
                "port": 8085,
                "youtube_api": "configured" if youtube_api_key else "missing",
                "gemini_api": "configured" if gemini_api_key else "missing",
            }
        )

    @fallback_app.route("/info")
    def info():
        return jsonify(
            {
                "python_version": sys.version,
                "working_directory": os.getcwd(),
                "environment_variables": {
                    "PORT": os.getenv("PORT"),
                    "YOUTUBE_API_KEY": "configured" if youtube_api_key else "missing",
                    "GEMINI_API_KEY": "configured" if gemini_api_key else "missing",
                },
            }
        )

    print("Fallback server starting on port 8085...")
    fallback_app.run(host="127.0.0.1", port=8085, debug=False)
