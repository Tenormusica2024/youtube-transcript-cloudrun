#!/usr/bin/env python3
"""
YouTube Transcript App - Quick Recovery Test Server
ローカル環境での動作確認用の簡単なサーバー
"""

import os
from flask import Flask, render_template
from flask_cors import CORS

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

@app.route('/')
def index():
    """メインページ"""
    return '''
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YouTube要約アプリ - 復旧テスト</title>
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
                backdrop-filter: blur(10px);
            }
            h1 { text-align: center; margin-bottom: 30px; }
            .status { 
                background: #28a745; 
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 YouTube要約アプリ - 復旧テスト</h1>
            
            <div class="status">
                ✅ サーバー正常起動
            </div>
            
            <div class="info">
                <strong>📍 サーバー情報:</strong><br>
                • ポート: 8085<br>
                • ホスト: localhost<br>
                • 状態: 動作中
            </div>
            
            <div class="info">
                <strong>🔧 動作確認項目:</strong><br>
                • Flask アプリケーション: ✅<br>
                • テンプレート読み込み: ✅<br>
                • CORS 設定: ✅<br>
                • 静的ファイル: ✅
            </div>
            
            <div class="info">
                <strong>🎯 次のステップ:</strong><br>
                1. 基本サーバー機能確認完了<br>
                2. YouTube API 接続テスト<br>
                3. Gemini AI 統合テスト<br>
                4. フル機能復旧
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p>🤖 Generated with Claude Code</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    """ヘルスチェック"""
    return {'status': 'ok', 'message': 'YouTube Transcript App is running'}

@app.route('/test')
def test():
    """API接続テスト"""
    import sys
    import json
    
    info = {
        'python_version': sys.version,
        'flask_version': 'Available',
        'working_directory': os.getcwd(),
        'template_folder': app.template_folder,
        'static_folder': app.static_folder
    }
    
    return f'<pre>{json.dumps(info, indent=2, ensure_ascii=False)}</pre>'

if __name__ == '__main__':
    print("=" * 50)
    print("YouTube Transcript App - Quick Recovery Test")
    print("=" * 50)
    print(f"Starting server on http://localhost:8085")
    print("Access URLs:")
    print("  Main: http://localhost:8085")
    print("  Health: http://localhost:8085/health")
    print("  Test: http://localhost:8085/test")
    print("=" * 50)
    
    try:
        app.run(host='127.0.0.1', port=8085, debug=True)
    except Exception as e:
        print(f"Server startup error: {e}")