#\!/bin/bash

# YouTube Transcript App - Cloud Run Complete Deploy Script
# Google Cloud Shell で実行してください

echo '🚀 YouTube Transcript App デプロイ開始'

# ディレクトリ作成
mkdir -p youtube-transcript-app && cd youtube-transcript-app

# app.py作成
cat > app.py << 'APPEOF'

"""
YouTube Transcript Extractor - Cloud Run版
ポート干渉を避け、固定URLで動作するバージョン
"""

import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import googleapiclient.discovery
import googleapiclient.errors

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask アプリケーション設定
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Cloud Runでのクロスオリジン対応

# 環境変数読み込み
load_dotenv()

# Cloud Run用ポート設定（環境変数PORTを優先）
PORT = int(os.environ.get('PORT', 8080))

# APIキー取得（環境変数を優先）
def get_youtube_api_key():
    """YouTube API キーを取得"""
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        # .envファイルから取得を試みる
        api_key = os.getenv('YOUTUBE_API_KEY')
    
    if not api_key:
        logger.error("YouTube API key not found in environment variables")
        raise ValueError("YouTube APIキーが設定されていません。環境変数YOUTUBE_API_KEYを設定してください。")
    
    return api_key

# YouTube Data API v3の初期化
try:
    API_KEY = get_youtube_api_key()
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    logger.info("YouTube API client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize YouTube API client: {e}")
    youtube = None

def get_video_id(url):
    """YouTube URLから動画IDを抽出"""
    try:
        parsed_url = urlparse(url)
        
        # youtu.be形式
        if parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        
        # youtube.com形式
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                params = parse_qs(parsed_url.query)
                return params.get('v', [None])[0]
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            if parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
        
        raise ValueError(f"無効なYouTube URLです: {url}")
    except Exception as e:
        logger.error(f"Error extracting video ID from URL {url}: {e}")
        raise

def get_video_title(video_id):
    """動画タイトルを取得"""
    if not youtube:
        return "YouTube API未設定"
    
    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()
        
        if 'items' in response and len(response['items']) > 0:
            title = response['items'][0]['snippet']['title']
            logger.info(f"Retrieved title for video {video_id}: {title}")
            return title
        else:
            logger.warning(f"No title found for video {video_id}")
            return "タイトルを取得できませんでした"
    except Exception as e:
        logger.error(f"Error getting video title for {video_id}: {e}")
        return "タイトル取得エラー"

def get_transcript(video_id, lang='ja'):
    """字幕を取得"""
    try:
        # test_transcript_only.pyで動作していた実装を参考
        api = YouTubeTranscriptApi()
        
        # 直接fetch methodを試す
        try:
            transcript_obj = api.fetch(video_id, languages=[lang])
            transcript = transcript_obj.to_raw_data()
            logger.info(f"Found transcript in {lang} for video {video_id}")
        except Exception:
            try:
                # 英語で再試行
                transcript_obj = api.fetch(video_id, languages=['en'])
                transcript = transcript_obj.to_raw_data()
                logger.info(f"Found transcript in English for video {video_id}")
            except Exception:
                # 古いAPIスタイルでフォールバック
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang, 'en'])
                logger.info(f"Found transcript using legacy API for video {video_id}")
        
        return transcript
        
    except TranscriptsDisabled:
        error_msg = "この動画の字幕は無効化されています。"
        logger.warning(f"Transcripts disabled for video {video_id}")
        raise ValueError(error_msg)
    except NoTranscriptFound:
        error_msg = "指定された言語の字幕が見つかりません。"
        logger.warning(f"No transcript found for video {video_id} in language {lang}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"字幕の取得に失敗しました: {str(e)}"
        logger.error(f"Error fetching transcript for video {video_id}: {e}")
        raise ValueError(error_msg)

def format_transcript(transcript, format_type='txt'):
    """字幕をフォーマット"""
    if format_type == 'json':
        return json.dumps(transcript, ensure_ascii=False, indent=2)
    elif format_type == 'srt':
        # SRT形式（タイムスタンプ付き）
        srt_content = []
        for i, item in enumerate(transcript, 1):
            start = format_timestamp(item['start'])
            end = format_timestamp(item['start'] + item['duration'])
            srt_content.append(f"{i}\n{start} --> {end}\n{item['text']}\n")
        return '\n'.join(srt_content)
    else:
        # デフォルト: プレーンテキスト
        return '\n'.join([item['text'] for item in transcript])

def format_timestamp(seconds):
    """秒数をSRTタイムスタンプ形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')

@app.route('/health')
def health():
    """ヘルスチェックエンドポイント（Cloud Run用）"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'youtube_api': 'configured' if youtube else 'not configured'
    })

@app.route('/extract', methods=['POST'])
def extract():
    """字幕抽出エンドポイント"""
    try:
        data = request.json
        url = data.get('url')
        lang = data.get('lang', 'ja')
        format_type = data.get('format', 'txt')
        
        if not url:
            return jsonify({'error': 'URLが指定されていません'}), 400
        
        # 動画ID取得
        video_id = get_video_id(url)
        logger.info(f"Processing video: {video_id}")
        
        # タイトル取得
        title = get_video_title(video_id)
        
        # 字幕取得
        transcript = get_transcript(video_id, lang)
        
        # フォーマット
        formatted_transcript = format_transcript(transcript, format_type)
        
        # 統計情報
        stats = {
            'total_segments': len(transcript),
            'total_duration': sum(item['duration'] for item in transcript),
            'language': lang
        }
        
        response_data = {
            'success': True,
            'video_id': video_id,
            'title': title,
            'transcript': formatted_transcript,
            'stats': stats
        }
        
        logger.info(f"Successfully processed video {video_id}")
        return jsonify(response_data)
        
    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'success': False, 'error': '予期しないエラーが発生しました'}), 500

@app.route('/supported_languages/<video_id>')
def supported_languages(video_id):
    """利用可能な言語のリストを取得"""
    try:
        # 新しいAPIと古いAPIの両方を試す
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
        except AttributeError:
            # 古いAPIを使用
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        languages = []
        for transcript in transcript_list:
            languages.append({
                'code': transcript.language_code,
                'name': transcript.language,
                'is_generated': transcript.is_generated,
                'is_translatable': transcript.is_translatable
            })
        
        return jsonify({
            'success': True,
            'languages': languages
        })
    except Exception as e:
        logger.error(f"Error getting supported languages for {video_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    """404エラーハンドラー"""
    return jsonify({'error': 'エンドポイントが見つかりません'}), 404

@app.errorhandler(500)
def server_error(e):
    """500エラーハンドラー"""
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'サーバーエラーが発生しました'}), 500

if __name__ == '__main__':
    # Cloud Run環境かローカル環境かを判定
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    if is_cloud_run:
        logger.info(f"Starting Cloud Run server on port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        # ローカル開発環境
        logger.info(f"Starting local development server on port {PORT}")
        app.run(host='127.0.0.1', port=PORT, debug=True)
APPEOF

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

# システムパッケージを更新し、必要なツールをインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY app.py .
COPY templates/ templates/

# 非rootユーザーを作成
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# ポート設定（Cloud Runが動的に設定）
ENV PORT=8080
EXPOSE $PORT

# Gunicornでアプリケーションを起動
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
EOF

# templates/index.html作成
mkdir templates
cat > templates/index.html << 'HTMLEOF'
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
HTMLEOF

echo "📁 ファイル作成完了"

# Google Cloud APIs を有効化
echo "⚙️ Google Cloud APIs 有効化中..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com

echo "🚀 Cloud Run デプロイ開始..."

# Cloud Run にデプロイ
gcloud run deploy youtube-transcript \
  --source . \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --set-env-vars YOUTUBE_API_KEY=AIzaSyAHkhiqjoRBRWx_HMlP7V_HeyzCc4Yn7rw \
  --port 8080 \
  --memory 512Mi \
  --timeout 300

echo ""
echo "🎉 デプロイ完了！"
echo ""
echo "📋 デプロイされたサービスURL:"
gcloud run services describe youtube-transcript \
  --platform managed \
  --region asia-northeast1 \
  --format 'value(status.url)'

echo ""
echo "✅ 次のステップ:"
echo "1. 上記URLにブラウザでアクセス"
echo "2. YouTube動画URLで字幕抽出をテスト"
echo "3. /health エンドポイントでヘルスチェック確認"
echo ""
echo "🎯 テスト用YouTube URL例:"
echo "  https://www.youtube.com/watch?v=jNQXAC9IVRw (英語)"
echo "  https://www.youtube.com/watch?v=dQw4w9WgXcQ (英語)"
echo ""