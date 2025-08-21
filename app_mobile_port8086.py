"""
YouTube Transcript Extractor - Mobile Version (Port 8086)
ポート競合回避版
"""

import base64
import json
import logging
import os
import socket
import time
from datetime import datetime
from io import BytesIO
from urllib.parse import parse_qs, urlparse

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# 最小限の依存関係でまず動作確認
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask アプリケーション設定
app = Flask(__name__, template_folder="templates", static_folder="static")

# CORS設定
CORS(app, origins=["*"], supports_credentials=True)

# ポート設定（競合回避）
PORT = 8086


def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_video_id(url):
    """YouTube URLから動画IDを抽出（簡易版）"""
    try:
        parsed_url = urlparse(url)

        # youtu.be形式
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]

        # youtube.com形式
        if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                return params.get("v", [None])[0]

        raise ValueError(f"無効なYouTube URLです: {url}")
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        raise


@app.route("/")
def index():
    """メインページ（最小限バージョン）"""
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube字幕抽出ツール - スマホ版 (Port 8086)</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
        
        <style>
            :root {
                --youtube-red: #ff0000;
                --youtube-gradient: linear-gradient(135deg, #ff4757 0%, #ff3742 100%);
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
                min-height: 100vh;
            }
            
            .navbar {
                background: var(--youtube-gradient);
                padding: 1rem;
                box-shadow: 0 4px 20px rgba(255, 0, 0, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .navbar::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 200%;
                height: 100%;
                background: 
                    radial-gradient(ellipse 280px 180px at 40% 30%, rgba(255, 90, 95, 0.3) 0%, transparent 40%),
                    radial-gradient(ellipse 200px 140px at 70% 60%, rgba(255, 100, 100, 0.25) 0%, transparent 45%);
                animation: waterReflection 20s ease-in-out infinite;
                pointer-events: none;
            }
            
            @keyframes waterReflection {
                0%, 100% { transform: translateX(0) scale(1); opacity: 0.6; }
                25% { transform: translateX(10%) scale(1.05); opacity: 0.8; }
                50% { transform: translateX(-5%) scale(0.98); opacity: 0.7; }
                75% { transform: translateX(15%) scale(1.02); opacity: 0.9; }
            }
            
            .navbar-brand {
                color: white !important;
                font-size: 1.3rem;
                font-weight: 700;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                display: flex;
                align-items: center;
                gap: 10px;
                z-index: 1;
                position: relative;
            }
            
            .main-card {
                background: white;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
                margin: 1rem;
                overflow: hidden;
            }
            
            .card-header-custom {
                background: linear-gradient(135deg, #ff6b7a 0%, #ff4757 100%);
                color: white;
                padding: 1.5rem;
                text-align: center;
            }
            
            .status-card {
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
                border-left: 4px solid #28a745;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem;
            }
        </style>
    </head>
    <body>
        <nav class="navbar">
            <div class="container-fluid">
                <span class="navbar-brand">
                    <i class="bi bi-youtube"></i>
                    YouTube字幕抽出ツール - スマホ版 (Port 8086)
                </span>
            </div>
        </nav>
        
        <div class="status-card">
            <h4><i class="bi bi-check-circle-fill text-success"></i> サーバー起動成功</h4>
            <p><strong>ポート:</strong> 8086 (競合回避版)</p>
            <p><strong>ステータス:</strong> ✅ 正常動作中</p>
            <p><strong>赤基調水面反射エフェクト:</strong> ✅ 動作中</p>
        </div>
        
        <div class="main-card">
            <div class="card-header-custom">
                <h2>基本動作確認完了</h2>
            </div>
            <div class="card-body p-4">
                <div class="alert alert-success">
                    <h6><i class="bi bi-check-circle"></i> 確認項目:</h6>
                    <ul class="mb-0">
                        <li>✅ Flask サーバー起動</li>
                        <li>✅ ポート8086バインド</li>
                        <li>✅ 赤基調UIテーマ</li>
                        <li>✅ 水面反射アニメーション</li>
                        <li>✅ レスポンシブデザイン</li>
                    </ul>
                </div>
                
                <div class="alert alert-info">
                    <h6><i class="bi bi-info-circle"></i> 次のステップ:</h6>
                    <p class="mb-2">基本動作が確認できたら、YouTube字幕抽出機能を追加します</p>
                    <ol class="mb-0">
                        <li>依存関係の段階的追加</li>
                        <li>YouTube API統合</li>
                        <li>Gemini AI統合</li>
                    </ol>
                </div>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """


@app.route("/health")
def health():
    """ヘルスチェック"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "port": PORT,
            "message": "YouTube字幕抽出ツール - スマホ版 (Port 8086)",
        }
    )


@app.route("/test")
def test():
    """テスト用URL抽出"""
    test_url = request.args.get("url", "")
    if test_url:
        try:
            video_id = get_video_id(test_url)
            return jsonify(
                {
                    "success": True,
                    "url": test_url,
                    "video_id": video_id,
                    "message": "URL解析成功",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 400
    else:
        return jsonify(
            {"message": "テスト用: ?url=https://www.youtube.com/watch?v=VIDEO_ID"}
        )


if __name__ == "__main__":
    local_ip = get_local_ip()

    print("\n" + "=" * 60)
    print("🎬 YouTube Transcript Extractor - Mobile Version (Port 8086)")
    print("=" * 60)
    print(f"🚀 Starting server on port {PORT}...")
    print(f"📱 Access URLs:")
    print(f"   Local:    http://127.0.0.1:{PORT}")
    print(f"   Network:  http://{local_ip}:{PORT}")
    print(
        f"🔥 Test:     http://127.0.0.1:{PORT}/test?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    print("=" * 60 + "\n")

    try:
        app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        input("Enterキーで終了...")
