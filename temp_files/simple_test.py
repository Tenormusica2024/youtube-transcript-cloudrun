#!/usr/bin/env python
"""
Simple test server to check basic Flask functionality on port 8085
"""

import sys

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return """
    <html>
    <head>
        <title>YouTube字幕抽出ツール - 簡単テスト</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .status { color: #28a745; font-weight: bold; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 YouTube字幕抽出ツール - 簡単テスト</h1>
            <p class="status">✅ Flask サーバーは正常に動作しています</p>
            <p><strong>ポート:</strong> 8085</p>
            <p><strong>URL:</strong> http://localhost:8085</p>
            <p><strong>この画面が表示されれば基本的なFlaskサーバーは動作しています</strong></p>
        </div>
    </body>
    </html>
    """


@app.route("/health")
def health():
    return {"status": "ok", "port": 8085, "message": "Simple test server running"}


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 YouTube字幕抽出ツール - 簡単テスト")
    print("=" * 50)
    print("🚀 ポート8085で起動中...")
    print("📱 アクセス: http://localhost:8085")
    print("=" * 50)

    try:
        app.run(host="0.0.0.0", port=8085, debug=True, use_reloader=False)
    except Exception as e:
        print(f"❌ エラー: {e}")
        print("詳細:")
        import traceback

        traceback.print_exc()
        input("エラーが発生しました。Enterキーを押して終了...")
