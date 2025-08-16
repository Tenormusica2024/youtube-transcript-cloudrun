"""
YouTube Transcript Extractor - スマホ対応版（ngrok対応）
メルカリアナライザーのノウハウを活用した改良版
"""

import json
import logging
import os
import random
import socket
import time
import qrcode
import io
import base64
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs, urlparse

import google.generativeai as genai
import googleapiclient.discovery
import googleapiclient.errors
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask アプリの初期化
app = Flask(__name__)

# CORS設定（ngrok対応）
CORS(app, origins=[
    "http://localhost:8085",
    "http://127.0.0.1:8085", 
    "https://*.ngrok-free.app",
    "https://*.ngrok.app"
], supports_credentials=True)

# ngrok URL管理用
CURRENT_NGROK_URL = "https://e87595a466f4.ngrok-free.app"

def get_ngrok_url():
    """ngrok APIから現在のURLを動的取得"""
    try:
        # ngrok APIエンドポイント（ローカル）
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    public_url = tunnel.get("public_url")
                    if public_url:
                        logger.info(f"動的ngrok URL取得成功: {public_url}")
                        return public_url
        logger.warning("ngrok API応答なし - 固定URLを使用")
        return CURRENT_NGROK_URL
    except Exception as e:
        logger.warning(f"ngrok URL動的取得失敗: {e} - 固定URLを使用")
        return CURRENT_NGROK_URL

def get_local_ip():
    """ローカルIPアドレスを取得"""
    try:
        # Googleの8.8.8.8に接続してローカルIPを取得
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def generate_qr_code(url):
    """QRコード生成"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Base64エンコード
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return None

def get_ai_api_key():
    """AI APIキーを取得"""
    # 直接指定されたAPIキーを使用
    api_key = "AIzaSyBKVL0MW3hbTFX7llfbuF0TL73SKNR2Rfw"
    
    # 環境変数からも取得を試行
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        logger.warning("AI API key not found - using basic formatting")
        return None
    
    logger.info("AI API key configured successfully")
    return api_key

def format_with_ai(text, api_key):
    """AIでテキストを整形"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        
        # より明確な整形指示プロンプト（以前の成功版に基づく）
        prompt = f"""YouTube字幕の整形処理を実行してください。

以下の字幕テキストを読みやすく整形し、詳細な要約を作成してください：

【字幕内容】
{text}

【整形要求】
・適切な段落分けを行う（2-3文ごとに改行）
・繰り返し表現や不自然な接続を修正
・読みやすい日本語文章にする
・必ず行間スペースを入れる（段落間は空行を挿入）

【要約要求】
・内容を8-12行程度で詳しくまとめる
・重要なポイントを5-7個の箇条書きにする
・具体的な数値、名称、事例を含める
・話の流れと結論を明確に示す
・背景情報や文脈も含める

【回答形式】
整形後テキスト：

[ここに段落分けされた読みやすいテキスト]

要約：

■ 概要
[全体の内容を2-3行で説明]

■ 主要ポイント
• [ポイント1: 具体的な内容]
• [ポイント2: 具体的な内容]
• [ポイント3: 具体的な内容]
• [ポイント4: 具体的な内容]
• [ポイント5: 具体的な内容]

■ 詳細情報
[追加の重要な情報や補足説明を3-4行]

■ 結論・まとめ
[動画の結論や重要なメッセージを2-3行]"""
        
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=8000,  # 整形済みテキストが見切れないよう大幅に増量
                top_p=0.8,
            ),
        )
        
        return response.text
    except Exception as e:
        logger.error(f"AI整形エラー: {e}")
        return text

def format_text_basic(text):
    """基本的なテキスト整形（AI不使用版）"""
    try:
        import re
        
        # 基本的な整形処理
        formatted_text = text
        
        # 重複する単語を削除
        words = formatted_text.split()
        seen = set()
        unique_words = []
        for word in words:
            if word.lower() not in seen:
                unique_words.append(word)
                seen.add(word.lower())
        formatted_text = ' '.join(unique_words)
        
        # 適切な句読点を追加
        formatted_text = re.sub(r'([。！？])([あ-ん])', r'\1\n\2', formatted_text)
        formatted_text = re.sub(r'([a-zA-Z0-9])([あ-ん])', r'\1 \2', formatted_text)
        formatted_text = re.sub(r'([あ-ん])([A-Z])', r'\1 \2', formatted_text)
        
        # 長い文を段落に分割
        sentences = formatted_text.split('。')
        paragraphs = []
        current_paragraph = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                current_paragraph.append(sentence + '。')
                # 3文ごとに段落分け
                if len(current_paragraph) >= 3:
                    paragraphs.append(''.join(current_paragraph))
                    current_paragraph = []
        
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph))
        
        # 最終整形
        result = '\n\n'.join(paragraphs)
        
        # 簡単な要約を追加
        result += f"\n\n【要約】\n上記は YouTube 動画の字幕内容を整形したものです。詳細な要約には AI API の設定が必要です。"
        
        return result
        
    except Exception as e:
        logger.error(f"基本整形エラー: {e}")
        return text

def extract_youtube_transcript(video_url, language_code='ja'):
    """YouTube字幕抽出"""
    try:
        # Video IDを抽出
        parsed_url = urlparse(video_url)
        if 'youtube.com' in parsed_url.netloc:
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path[1:]
        else:
            raise ValueError("有効なYouTube URLではありません")
        
        if not video_id:
            raise ValueError("動画IDを取得できませんでした")
        
        logger.info(f"動画ID: {video_id} の字幕を取得中...")
        
        # 字幕取得 - 新API方式を使用
        try:
            # YouTubeTranscriptApiインスタンスを作成
            ytt_api = YouTubeTranscriptApi()
            
            # 言語フォールバック順序
            languages_to_try = [language_code, 'en'] if language_code != 'auto' else ['ja', 'en']
            
            # 字幕データ取得
            transcript_data = ytt_api.fetch(video_id, languages=languages_to_try)
            
            # テキストを結合（新形式対応）
            full_text = ' '.join([entry.text for entry in transcript_data])
            
            logger.info(f"字幕取得成功 (動画ID: {video_id})")
            return {
                'success': True,
                'transcript': full_text,
                'language': transcript_data.language_code if hasattr(transcript_data, 'language_code') else 'unknown',
                'video_id': video_id
            }
            
        except Exception as e:
            logger.warning(f"字幕取得失敗: {e}")
            # 最後の手段として利用可能な最初の字幕を取得
            try:
                transcript_list = ytt_api.list(video_id)
                for transcript in transcript_list:
                    try:
                        transcript_data = transcript.fetch()
                        full_text = ' '.join([entry.text for entry in transcript_data])
                        
                        logger.info(f"字幕取得成功 (言語: {transcript.language_code})")
                        return {
                            'success': True,
                            'transcript': full_text,
                            'language': transcript.language_code,
                            'video_id': video_id
                        }
                    except Exception as inner_e:
                        logger.warning(f"字幕フェッチ失敗 ({transcript.language_code}): {inner_e}")
                        continue
            except Exception as list_e:
                logger.error(f"字幕リスト取得失敗: {list_e}")
        
        raise Exception("利用可能な字幕が見つかりませんでした")
        
    except Exception as e:
        logger.error(f"字幕抽出エラー: {e}")
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    """メインページ"""
    return render_template('index_mobile.html')

@app.route('/api/access-info')
def get_access_info():
    """アクセス情報取得API"""
    try:
        local_ip = get_local_ip()
        port = 8085
        
        # 動的ngrok URL取得
        dynamic_ngrok_url = get_ngrok_url()
        
        access_info = {
            'localURL': f'http://127.0.0.1:{port}',
            'networkURL': f'http://{local_ip}:{port}',
            'domainURL': f'http://youtube-extractor.local:{port}',
            'ngrokURL': dynamic_ngrok_url or 'ngrokトンネルが起動していません'
        }
        
        return jsonify({
            'success': True,
            'data': access_info
        })
    except Exception as e:
        logger.error(f"アクセス情報取得エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/extract', methods=['POST'])
def extract_transcript():
    """字幕抽出API"""
    try:
        data = request.get_json()
        video_url = data.get('url', '')
        language = data.get('language', 'ja')
        format_text = data.get('format', True)
        
        if not video_url:
            return jsonify({
                'success': False,
                'error': 'YouTube URLが指定されていません'
            }), 400
        
        logger.info(f"字幕抽出開始: {video_url}")
        
        # 字幕抽出
        result = extract_youtube_transcript(video_url, language)
        
        if not result['success']:
            return jsonify(result), 400
        
        # テキスト整形
        formatted_text = result['transcript']
        if format_text:
            try:
                api_key = get_ai_api_key()
                if api_key:
                    formatted_text = format_with_ai(result['transcript'], api_key)
                    logger.info("AI整形成功")
                else:
                    formatted_text = format_text_basic(result['transcript'])
                    logger.info("基本整形を使用")
            except Exception as e:
                logger.warning(f"整形処理失敗: {e}")
                # 整形失敗時は基本整形を試行
                formatted_text = format_text_basic(result['transcript'])
        
        # 要約と整形テキストを分離
        summary_text = ""
        cleaned_formatted_text = formatted_text
        
        if format_text and "要約" in formatted_text:
            # 要約部分を抽出
            if "要約：" in formatted_text:
                parts = formatted_text.split("要約：", 1)
                if len(parts) > 1:
                    summary_text = parts[1].strip()
                    # 整形テキストから要約部分を除去
                    cleaned_formatted_text = parts[0].replace("整形後テキスト：", "").strip()
            elif "【要約】" in formatted_text:
                parts = formatted_text.split("【要約】", 1)
                if len(parts) > 1:
                    summary_text = parts[1].strip()
                    cleaned_formatted_text = parts[0].replace("整形後テキスト：", "").strip()
        
        # 不要な接頭辞や定型文を削除
        cleaned_formatted_text = cleaned_formatted_text.replace("**整形後テキスト：**", "")
        cleaned_formatted_text = cleaned_formatted_text.replace("整形後テキスト：", "")
        cleaned_formatted_text = cleaned_formatted_text.replace("はい、承知いたしました。以下に整形後のテキストと要約を記載します。", "")
        cleaned_formatted_text = cleaned_formatted_text.replace("はい、承知いたしました。", "")
        cleaned_formatted_text = cleaned_formatted_text.replace("以下に整形後のテキストと要約を示します。", "")
        cleaned_formatted_text = cleaned_formatted_text.strip()
        
        # 要約からも不要な文言を削除
        if summary_text:
            summary_text = summary_text.replace("はい、承知いたしました。", "")
            summary_text = summary_text.replace("以下に要約を記載します。", "")
            summary_text = summary_text.strip()
        
        return jsonify({
            'success': True,
            'data': {
                'original_transcript': result['transcript'],
                'formatted_transcript': cleaned_formatted_text,
                'summary': summary_text,
                'language': result['language'],
                'video_id': result['video_id']
            }
        })
        
    except Exception as e:
        logger.error(f"字幕抽出API エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/qr-code')
def generate_qr():
    """QRコード生成エンドポイント"""
    try:
        # 動的ngrok URL取得してQRコード生成
        default_url = get_ngrok_url() or 'http://127.0.0.1:8085'
        url = request.args.get('url', default_url)
        qr_code_data = generate_qr_code(url)
        
        if qr_code_data:
            return jsonify({
                'success': True,
                'qr_code': qr_code_data,
                'url': url
            })
        else:
            return jsonify({
                'success': False,
                'error': 'QRコード生成に失敗しました'
            }), 500
            
    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """ヘルスチェック"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ngrok_url': get_ngrok_url()
    })

def setup_ngrok_url():
    """ngrok URL設定"""
    global CURRENT_NGROK_URL
    # 実際のngrok URLをここで設定（ngrok起動後に更新）
    # 例: CURRENT_NGROK_URL = "https://abc123.ngrok-free.app"
    pass

if __name__ == '__main__':
    setup_ngrok_url()
    logger.info("🚀 YouTube字幕抽出サーバー（スマホ対応版）を起動中...")
    logger.info(f"📱 アクセスURL: http://127.0.0.1:8085")
    if CURRENT_NGROK_URL:
        logger.info(f"🌐 ngrok URL: {CURRENT_NGROK_URL}")
    
    # サーバー起動
    app.run(
        host='0.0.0.0',
        port=8085,
        debug=True,
        threaded=True
    )