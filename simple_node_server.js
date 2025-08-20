const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8091;

const server = http.createServer((req, res) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
    
    // CORSヘッダー
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.url === '/' || req.url === '/index.html') {
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        res.end(`
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node.js HTTPサーバー - ポート解放確認</title>
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
            max-width: 500px;
        }
        .success { 
            color: #00ff00; 
            font-weight: bold; 
            font-size: 28px; 
            margin: 20px 0;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 YouTube字幕抽出ツール</h1>
        <p class="success pulse">✅ Node.js HTTPサーバー起動成功</p>
        
        <div class="info">
            <strong>ポート:</strong> ${PORT}<br>
            <strong>プロトコル:</strong> HTTP<br>
            <strong>ステータス:</strong> 正常稼働中
        </div>
        
        <div class="info">
            <strong>時刻:</strong> <span id="time"></span><br>
            <strong>アクセスURL:</strong> http://localhost:${PORT}
        </div>
        
        <p><strong>✅ ポート解放成功</strong></p>
        <p>次のステップ: FlaskでYouTube字幕抽出機能を追加</p>
    </div>
    
    <script>
        function updateTime() {
            document.getElementById('time').textContent = new Date().toLocaleString('ja-JP');
        }
        updateTime();
        setInterval(updateTime, 1000);
        
        // 接続確認
        console.log('Node.js server connected successfully');
        fetch('/health')
            .then(response => response.json())
            .then(data => console.log('Health check:', data))
            .catch(err => console.log('Health check failed:', err));
    </script>
</body>
</html>
        `);
    } else if (req.url === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
            status: 'ok',
            port: PORT,
            timestamp: new Date().toISOString(),
            message: 'Node.js server running'
        }));
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

server.listen(PORT, '0.0.0.0', () => {
    console.log('='.repeat(60));
    console.log('🚀 Node.js HTTPサーバー起動成功');
    console.log('='.repeat(60));
    console.log(`📱 アクセスURL: http://localhost:${PORT}`);
    console.log(`🌐 ネットワーク: http://0.0.0.0:${PORT}`);
    console.log(`⏰ 起動時刻: ${new Date().toLocaleString('ja-JP')}`);
    console.log('='.repeat(60));
});

server.on('error', (err) => {
    console.error('❌ サーバーエラー:', err);
    if (err.code === 'EADDRINUSE') {
        console.error(`ポート ${PORT} は既に使用されています`);
    }
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n📴 サーバーを停止中...');
    server.close(() => {
        console.log('✅ サーバーが正常に停止しました');
        process.exit(0);
    });
});