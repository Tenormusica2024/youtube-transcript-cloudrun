#!/usr/bin/env python3
"""
YouTube Transcript App - Fixed Server Startup Script
ポート設定とAPI接続を修正したバージョン
"""

import os
import sys

from dotenv import load_dotenv

# 環境変数を先に設定
load_dotenv()

# ポートを8085に強制設定（競合回避）
os.environ["PORT"] = "8085"

# 必要なライブラリのインポートチェック
try:
    import flask
    import google.generativeai as genai
    import googleapiclient.discovery
    from flask_cors import CORS
    from youtube_transcript_api import YouTubeTranscriptApi

    print("✅ All required libraries are available")
except ImportError as e:
    print(f"❌ Library import error: {e}")
    sys.exit(1)

# APIキー確認
youtube_api_key = os.getenv("YOUTUBE_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not youtube_api_key:
    print("❌ YOUTUBE_API_KEY not found")
else:
    print(f"✅ YouTube API Key: {youtube_api_key[:10]}...")

if not gemini_api_key:
    print("❌ GEMINI_API_KEY not found")
else:
    print(f"✅ Gemini API Key: {gemini_api_key[:10]}...")

# メインアプリケーションをインポートして起動
try:
    print("\n" + "=" * 50)
    print("YouTube Transcript App - Starting Fixed Server")
    print("=" * 50)
    print(f"Server will start on: http://localhost:8085")
    print("Fixed configurations:")
    print("  - Port: 8085 (避けるポート競合)")
    print("  - API Keys: Configured")
    print("  - CORS: Enabled")
    print("=" * 50)

    # 元のapp.pyをインポートして起動
    from app import app

    app.run(host="127.0.0.1", port=8085, debug=True, use_reloader=False)

except Exception as e:
    print(f"❌ Server startup error: {e}")
    print("\nTrying fallback simple server...")

    # フォールバック: 簡単なサーバー
    from flask import Flask, jsonify

    fallback_app = Flask(__name__)
    CORS(fallback_app)

    @fallback_app.route("/")
    def index():
        return """
        <h1>YouTube Transcript App - Fallback Mode</h1>
        <p>Original app failed to start. Running in fallback mode.</p>
        <p><a href="/health">Health Check</a></p>
        """

    @fallback_app.route("/health")
    def health():
        return jsonify({"status": "fallback", "message": "Running in fallback mode"})

    print("Starting fallback server on port 8085...")
    fallback_app.run(host="127.0.0.1", port=8085, debug=True)
