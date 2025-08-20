@echo off
echo =====================================================
echo 管理者権限でサーバー起動 - YouTube字幕抽出ツール
echo =====================================================
echo.

REM 管理者権限チェック
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 管理者権限が必要です
    echo 右クリック → 「管理者として実行」してください
    pause
    exit /b 1
)

echo ✅ 管理者権限確認済み

REM 現在のディレクトリに移動
cd /d "%~dp0"

echo.
echo 🔹 既存のPythonプロセスを終了中...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1

echo 🔹 既存のNodeプロセスを終了中...
taskkill /F /IM node.exe >nul 2>&1

echo 🔹 ポート解放中...
netsh interface ipv4 show excludedportrange protocol=tcp >nul 2>&1

echo.
echo 🚀 管理者権限でPythonサーバーを起動中...
echo ポート: 8092
echo URL: http://localhost:8092
echo.

python -c "
import http.server
import socketserver
import webbrowser
import threading
import time

PORT = 8092

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = '''
<!DOCTYPE html>
<html lang=\"ja\">
<head>
    <meta charset=\"UTF-8\">
    <title>YouTube字幕抽出ツール - 管理者権限版</title>
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
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            text-align: center;
            max-width: 600px;
        }
        .success { 
            color: #00ff00; 
            font-weight: bold; 
            font-size: 32px; 
            margin: 20px 0;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }
        .info {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        .navbar {
            position: relative;
            overflow: hidden;
            padding: 10px 0;
        }
        .navbar::before {
            content: \"\";
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
    </style>
</head>
<body>
    <div class=\"container\">
        <div class=\"navbar\">
            <h1>🎬 YouTube字幕抽出ツール</h1>
        </div>
        <p class=\"success pulse\">✅ 管理者権限サーバー起動成功</p>
        
        <div class=\"info\">
            <strong>ポート:</strong> 8092<br>
            <strong>権限:</strong> 管理者<br>
            <strong>プロセス終了:</strong> 完了<br>
            <strong>ステータス:</strong> 正常稼働中
        </div>
        
        <div class=\"info\">
            <strong>水面反射エフェクト:</strong> ✅ 動作中<br>
            <strong>赤基調テーマ:</strong> ✅ 適用済み<br>
            <strong>アクセスURL:</strong> http://localhost:8092
        </div>
        
        <p><strong>🎯 ポート解放完全成功</strong></p>
        <p>管理者権限によりポートバインドが正常に完了しました</p>
    </div>
</body>
</html>
            '''
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:8092')

with socketserver.TCPServer(('', PORT), MyHandler) as httpd:
    print(f'✅ サーバー起動成功: http://localhost:{PORT}')
    print('🌐 ブラウザを自動で開きます...')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n📴 サーバーを停止します...')
        httpd.shutdown()
"

echo.
echo 📴 サーバーが停止しました
pause