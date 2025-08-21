#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/extract", methods=["POST"])
def extract():
    try:
        data = request.get_json()
        # 簡単なダミーレスポンス
        return jsonify(
            {
                "success": True,
                "title": "テスト動画",
                "transcript": "これはテスト用の字幕データです。",
                "summary": "AI要約: テスト用のサンプル要約です。",
                "stats": {"segments": 10, "characters": 1234, "language": "ja"},
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/access-info")
def access_info():
    return jsonify(
        {
            "localURL": "http://127.0.0.1:8088",
            "networkURL": "http://localhost:8088",
            "ngrokURL": "Not available",
        }
    )


@app.route("/qr-code")
def qr_code():
    return jsonify(
        {
            "success": True,
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
        }
    )


if __name__ == "__main__":
    print("YouTube Transcript App - Simple Server v1.3.11")
    print("=" * 55)
    print("Server URL: http://127.0.0.1:8088")
    print("Design: Red gradient with water reflection")
    print("Status: Running...")
    print("=" * 55)

    app.run(host="127.0.0.1", port=8088, debug=False)
