# YouTube Transcript Extractor - Complete Code Backup

## Project Overview
YouTube transcript extraction webapp with Gemini AI integration for text formatting and summarization. Deployed on Google Cloud Run with automatic CI/CD pipeline.

## Features
- YouTube transcript extraction with multi-language support
- Automatic text formatting with Gemini AI (periods followed by blank lines)
- Detailed summaries (500-800 characters) preserving information
- Web interface with real-time processing
- Cloud Run deployment with fixed URL
- Error handling and logging

## Complete Source Code

### app.py (Main Application)
```python
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
from google import genai
from google.genai import types

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

def get_gemini_api_key():
    """Gemini API キーを取得"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        # .envファイルから取得を試みる
        api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        logger.error("Gemini API key not found in environment variables")
        raise ValueError("Gemini APIキーが設定されていません。環境変数GEMINI_API_KEYを設定してください。")
    
    return api_key

# YouTube Data API v3の初期化
try:
    API_KEY = get_youtube_api_key()
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=API_KEY)
    logger.info("YouTube API client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize YouTube API client: {e}")
    youtube = None

# Gemini AI クライアントの初期化
try:
    GEMINI_API_KEY = get_gemini_api_key()
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Gemini API client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini API client: {e}")
    gemini_client = None

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
        # v1.2.2の正しいAPIを使用
        logger.info(f"Attempting to get transcript for video {video_id} in language {lang}")
        
        # APIインスタンスを作成
        api = YouTubeTranscriptApi()
        
        # fetchメソッドで字幕を取得
        fetched_transcript = api.fetch(video_id, languages=[lang])
        
        # FetchedTranscriptオブジェクトから生データを取得
        transcript = fetched_transcript.to_raw_data()
        
        logger.info(f"Found transcript in {lang} for video {video_id}, {len(transcript)} segments")
        return transcript
        
    except NoTranscriptFound:
        try:
            # 英語で再試行
            logger.info(f"Japanese transcript not found, trying English for video {video_id}")
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id, languages=['en'])
            transcript = fetched_transcript.to_raw_data()
                
            logger.info(f"Found transcript in English for video {video_id}, {len(transcript)} segments")
            return transcript
        except NoTranscriptFound:
            error_msg = "指定された言語の字幕が見つかりません（日本語・英語共に）。"
            logger.warning(f"No transcript found for video {video_id} in any language")
            raise ValueError(error_msg)
    except TranscriptsDisabled:
        error_msg = "この動画の字幕は無効化されています。"
        logger.warning(f"Transcripts disabled for video {video_id}")
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
        # デフォルト: プレーンテキスト（スペースで結合して自然な文章に）
        return ' '.join([item['text'] for item in transcript])

def format_timestamp(seconds):
    """秒数をSRTタイムスタンプ形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace('.', ',')

def format_text_with_gemini(text):
    """Gemini AIを使用してテキストを可読性良く整形"""
    if not gemini_client:
        logger.warning("Gemini client not initialized, returning original text")
        return text
    
    try:
        prompt = f"""以下のYouTube字幕テキストを読みやすく整形してください。

【重要な制約】:
- 文字や単語を一切変更・追加・削除しないでください
- 内容の要約や意訳は絶対に行わないでください
- 元のテキストの文字をそのまま保持してください

【整形作業】:
1. 各文（。で終わる文）の後には必ず空行を入れてください（改行2回）
2. つまり、句点の後は必ず空行で区切ってください
3. 話題が変わる箇所ではさらに空行を追加してください
4. 「で、」「それで、」「そして、」などの接続詞の前でも空行を入れてください
5. 長い文は読点（、）の位置で改行してください
6. 読みやすさを最優先に、空行を多めに使ってください

元のテキスト:
{text}

整形されたテキスト:"""

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
            )
        )
        
        formatted_text = response.text.strip()
        logger.info("Text formatted successfully using Gemini")
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting text with Gemini: {e}")
        return text

def summarize_with_gemini(text):
    """Gemini AIを使用してテキストを要約"""
    if not gemini_client:
        logger.warning("Gemini client not initialized, returning empty summary")
        return ""

    try:
        summary_prompt = f"""以下のYouTube動画の字幕テキストを詳細に要約してください。

【要約の要求】:
1. 重要な情報は全て残してください
2. 主要なトピックを5〜10個の要点に整理してください
3. 固有名詞、数値、専門用語は必ず含めてください
4. 具体的な例や説明も重要なものは残してください
5. 500〜800文字程度でまとめてください

【整形ルール】:
1. 各要点は「・」や「◆」で始めてください
2. 関連する内容は段落でグループ化してください
3. 重要なキーワードは【】で囲んでください
4. 各段落の間には空行を入れてください
5. 読みやすさを重視して改行を使ってください

字幕テキスト:
{text}

詳細な要約:"""

        response = gemini_client.models.generate_content(
            model='gemini-2.0-flash-001',
            contents=summary_prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=1200,
            )
        )
        
        summary = response.text.strip()
        logger.info("Text summarized successfully using Gemini")
        return summary
        
    except Exception as e:
        logger.error(f"Error summarizing text with Gemini: {e}")
        return ""

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
        'youtube_api': 'configured' if youtube else 'not configured',
        'gemini_api': 'configured' if gemini_client else 'not configured'
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
        
        # プレーンテキストの場合は自動でGemini AIで整形と要約
        summary_text = ""
        if format_type == 'txt' and gemini_client:
            try:
                logger.info("Auto-formatting transcript with Gemini AI")
                formatted_transcript = format_text_with_gemini(formatted_transcript)
                
                logger.info("Auto-summarizing transcript with Gemini AI")
                summary_text = summarize_with_gemini(formatted_transcript)
            except Exception as e:
                logger.warning(f"Auto-formatting/summarizing failed, using original text: {e}")
        
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
            'summary': summary_text,
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

@app.route('/format_text', methods=['POST'])
def format_text():
    """テキスト整形エンドポイント"""
    try:
        data = request.json
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'テキストが指定されていません'}), 400
        
        if not gemini_client:
            return jsonify({'error': 'Gemini APIが利用できません'}), 503
        
        # Gemini AIでテキストを整形
        formatted_text = format_text_with_gemini(text)
        
        response_data = {
            'success': True,
            'original_text': text,
            'formatted_text': formatted_text
        }
        
        logger.info("Text formatting completed successfully")
        return jsonify(response_data)
        
    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in format_text: {e}")
        return jsonify({'success': False, 'error': '予期しないエラーが発生しました'}), 500

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
```

### templates/index.html (Frontend UI)
```html
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
                        <h4>字幕テキスト（AI整形済み）:</h4>
                        <textarea id="transcriptText" readonly>${result_data.transcript}</textarea>
                        
                        <h4 style="margin-top: 20px;">詳細な要約:</h4>
                        <textarea id="summaryText" readonly style="height: 250px; background-color: #f0f8ff; font-size: 14px; line-height: 1.6;">${result_data.summary || '要約を生成中...'}</textarea>
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
```

### requirements.txt (Dependencies)
```
# Web Framework
Flask==2.3.3
flask-cors==4.0.0

# YouTube関連
google-api-python-client==2.100.0
google-auth==2.23.0
google-auth-httplib2==0.1.1
youtube-transcript-api==1.2.2

# Gemini AI
google-genai==1.29.0

# 環境変数管理
python-dotenv==1.0.0

# 本番サーバー
gunicorn==21.2.0

# ユーティリティ
requests==2.31.0

# オプション: Claude AI統合（将来の拡張用）
# anthropic==0.7.0
```

### Dockerfile (Container Configuration)
```dockerfile
# Python 3.10 slimイメージを使用（軽量化）
FROM python:3.10-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルのコピーと インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# 非rootユーザーの作成（セキュリティ向上）
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Cloud Runが使用する環境変数PORTを受け入れる
ENV PORT=8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT}/health')" || exit 1

# Gunicornで本番環境向けに起動
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

### cloudbuild.yaml (CI/CD Pipeline)
```yaml
# Cloud Build configuration for YouTube Transcript App
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID', '.']
  
  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'youtube-transcript'
      - '--image'
      - 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID'
      - '--region'
      - 'asia-northeast1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--port'
      - '8080'
      - '--memory'
      - '512Mi'
      - '--timeout'
      - '300s'
      - '--max-instances'
      - '10'
      - '--set-env-vars'
      - 'YOUTUBE_API_KEY=$$YOUTUBE_API_KEY,GEMINI_API_KEY=$$GEMINI_API_KEY'

# Store images in Google Container Registry
images:
  - 'gcr.io/$PROJECT_ID/youtube-transcript-app:$BUILD_ID'

# Configuration for build
options:
  logging: CLOUD_LOGGING_ONLY
```

### .env (Environment Variables - Template)
```
YOUTUBE_API_KEY=AIzaSyBC8mkp2FgNXRaFLerpgjMaLG4ri4-X25A
GEMINI_API_KEY=AIzaSyBKVL0MW3hbTFX7llfbuF0TL73SKNR2Rfw
```

## Deployment Configuration

### GitHub Repository
- URL: https://github.com/Tenormusica2024/youtube-transcript-cloudrun
- All source code has been pushed successfully

### Cloud Build Configuration
- Automatic deployment on GitHub push
- Environment variables configured: YOUTUBE_API_KEY, GEMINI_API_KEY
- Docker image building and pushing to Google Container Registry
- Cloud Run deployment to asia-northeast1 region

### API Keys Used
- YouTube Data API v3: AIzaSyBC8mkp2FgNXRaFLerpgjMaLG4ri4-X25A
- Google Gemini API: AIzaSyBKVL0MW3hbTFX7llfbuF0TL73SKNR2Rfw

## Technical Fixes Applied

### YouTube Transcript API Issues
1. **XML parsing error**: Fixed by upgrading youtube-transcript-api from 0.6.2 to 1.2.2
2. **Method not found error**: Fixed by using `api.fetch()` instead of `YouTubeTranscriptApi.get_transcript()`
3. **Object not subscriptable**: Fixed by using `fetched_transcript.to_raw_data()` to extract transcript data

### Gemini AI Integration
- Automatic text formatting with periods followed by blank lines
- Detailed summaries (500-800 characters) preserving important information
- Error handling for API failures

### Features Implemented
- Multi-language support (Japanese, English, Korean, Chinese)
- Multiple output formats (Text, JSON, SRT)
- Real-time transcript extraction and formatting
- Automatic summarization
- Health check endpoint for Cloud Run
- Comprehensive error handling and logging

## Status
✅ Complete codebase saved to Memory Bank
✅ GitHub repository updated with all files
✅ Ready for Cloud Build trigger setup
✅ Environment variables documented

This backup contains the complete, working code for the YouTube transcript extraction webapp with Gemini AI integration, ready for Cloud Run deployment.