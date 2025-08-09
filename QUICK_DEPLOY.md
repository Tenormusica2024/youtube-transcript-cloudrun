# 🚀 Cloud Run ワンコマンドデプロイ

## Google Cloud Shell で実行

### 1. Cloud Shell を開く
[https://shell.cloud.google.com/](https://shell.cloud.google.com/)

### 2. 以下をコピペして実行

```bash
# ディレクトリ作成
mkdir youtube-transcript-app && cd youtube-transcript-app

# app.py作成
cat > app.py << 'EOF'
# （上記のapp.pyの内容をここに貼り付け）
EOF

# requirements.txt作成  
cat > requirements.txt << 'EOF'
Flask==2.3.3
flask-cors==4.0.0
google-api-python-client==2.100.0
google-auth==2.23.0
google-auth-httplib2==0.1.1
youtube-transcript-api==0.6.2
python-dotenv==1.0.0
gunicorn==21.2.0
requests==2.31.0
EOF

# Dockerfile作成
cat > Dockerfile << 'EOF'
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates/ templates/
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
EOF

# templates/index.html作成
mkdir templates
cat > templates/index.html << 'EOF'
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"], select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            background-color: #ff0000;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
        }
        button:hover {
            background-color: #cc0000;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        #result {
            margin-top: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
        }
        .hidden {
            display: none;
        }
        .error {
            color: #ff0000;
            background-color: #ffe6e6;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ffcccc;
        }
        .success {
            color: #008000;
            background-color: #e6ffe6;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccffcc;
        }
        .loading {
            text-align: center;
            color: #666;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: monospace;
            resize: vertical;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>YouTube Transcript Extractor</h1>
        
        <form id="extractForm">
            <div class="form-group">
                <label for="url">YouTube URL:</label>
                <input type="text" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
            </div>
            
            <div class="form-group">
                <label for="lang">言語:</label>
                <select id="lang" name="lang">
                    <option value="ja">日本語</option>
                    <option value="en">English</option>
                    <option value="ko">한국어</option>
                    <option value="zh">中文</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="format">出力フォーマット:</label>
                <select id="format" name="format">
                    <option value="txt">テキスト</option>
                    <option value="json">JSON</option>
                    <option value="srt">SRT (字幕ファイル)</option>
                </select>
            </div>
            
            <button type="submit" id="submitBtn">字幕を抽出</button>
        </form>
        
        <div id="result" class="hidden">
            <h2>結果</h2>
            <div id="resultContent"></div>
        </div>
    </div>

    <script>
        document.getElementById('extractForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            
            // ボタンを無効化
            submitBtn.disabled = true;
            submitBtn.textContent = '処理中...';
            
            // 結果エリアを表示
            result.classList.remove('hidden');
            resultContent.innerHTML = '<div class="loading">字幕を取得中...</div>';
            
            try {
                const formData = new FormData(form);
                const data = {
                    url: formData.get('url'),
                    lang: formData.get('lang'),
                    format: formData.get('format')
                };
                
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result_data = await response.json();
                
                if (result_data.success) {
                    const stats = result_data.stats || {};
                    resultContent.innerHTML = `
                        <div class="success">
                            <h3>[OK] 抽出成功</h3>
                            <p><strong>タイトル:</strong> ${result_data.title || 'Unknown'}</p>
                            <p><strong>動画ID:</strong> ${result_data.video_id || 'Unknown'}</p>
                            <p><strong>セグメント数:</strong> ${stats.total_segments || 'Unknown'}</p>
                            <p><strong>総時間:</strong> ${Math.round(stats.total_duration || 0)} 秒</p>
                            <p><strong>言語:</strong> ${stats.language || 'Unknown'}</p>
                        </div>
                        <h4>字幕テキスト:</h4>
                        <textarea readonly>${result_data.transcript}</textarea>
                    `;
                } else {
                    resultContent.innerHTML = `
                        <div class="error">
                            <h3>[ERROR] エラー</h3>
                            <p>${result_data.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultContent.innerHTML = `
                    <div class="error">
                        <h3>[ERROR] 通信エラー</h3>
                        <p>サーバーとの通信でエラーが発生しました: ${error.message}</p>
                    </div>
                `;
            } finally {
                // ボタンを再有効化
                submitBtn.disabled = false;
                submitBtn.textContent = '字幕を抽出';
            }
        });
    </script>
</body>
</html>
EOF

# APIを有効化
gcloud services enable run.googleapis.com

# デプロイ実行
gcloud run deploy youtube-transcript \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars YOUTUBE_API_KEY=AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw \
  --port 8080 \
  --memory 512Mi \
  --timeout 300

# デプロイ完了後、URLを表示
echo "🎉 デプロイ完了！"
gcloud run services describe youtube-transcript \
  --platform managed \
  --region asia-northeast1 \
  --format 'value(status.url)'
```

### 3. ブラウザで確認
上記コマンドで表示されるURLにアクセス！

---

## 🎉 完了！

このスクリプトで完全なYouTube字幕抽出サービスがCloud Runにデプロイされます。