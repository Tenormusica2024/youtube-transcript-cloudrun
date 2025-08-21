#!/usr/bin/env python3
# Ultra Light Server - ポート解放最終確認版

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = 8099


class UltraLightHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()

            html = (
                """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>Ultra Light Server - ポート解放成功</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0;
            background: linear-gradient(135deg, #ff4757 0%, #ff3742 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container { 
            background: rgba(255, 255, 255, 0.1); 
            padding: 40px; 
            border-radius: 20px; 
            backdrop-filter: blur(10px);
            text-align: center;
        }
        .success { 
            color: #00ff00; 
            font-weight: bold; 
            font-size: 32px; 
            margin: 20px 0;
        }
        .water-effect {
            position: relative;
            overflow: hidden;
        }
        .water-effect::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: 
                radial-gradient(ellipse 300px 200px at 50% 50%, rgba(255, 90, 95, 0.4) 0%, transparent 50%);
            animation: waterMove 15s ease-in-out infinite;
            pointer-events: none;
        }
        @keyframes waterMove {
            0%, 100% { transform: translate(0, 0) scale(1); }
            33% { transform: translate(10px, -5px) scale(1.05); }
            66% { transform: translate(-8px, 8px) scale(0.98); }
        }
    </style>
</head>
<body>
    <div class="container water-effect">
        <h1>🎬 YouTube字幕抽出ツール</h1>
        <p class="success">✅ Ultra Light Server 起動成功</p>
        
        <div style="background: rgba(255, 255, 255, 0.2); padding: 15px; border-radius: 10px; margin: 15px 0;">
            <strong>ポート:</strong> """
                + str(PORT)
                + """<br>
            <strong>プロセス:</strong> Python HTTP Server<br>
            <strong>エフェクト:</strong> 赤基調水面反射<br>
            <strong>ステータス:</strong> 正常稼働中
        </div>
        
        <p><strong>🎯 ポート解放完全成功</strong></p>
        <p>最軽量サーバーによる動作確認済み</p>
    </div>
</body>
</html>"""
            )

            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        return  # ログ出力を抑制


def check_port_available(port):
    """ポートが利用可能か確認"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("localhost", port))
            return True
        except:
            return False


def main():
    if not check_port_available(PORT):
        print(f"❌ ポート {PORT} は既に使用されています")
        return False

    try:
        server = HTTPServer(("0.0.0.0", PORT), UltraLightHandler)
        print(f"🚀 Ultra Light Server 起動成功")
        print(f"📱 http://localhost:{PORT}")
        print(f"✅ 赤基調水面反射エフェクト有効")

        server.serve_forever()

    except KeyboardInterrupt:
        print("\n📴 サーバー停止")
        server.shutdown()
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("✅ 処理完了")
    else:
        print("❌ 処理失敗")
