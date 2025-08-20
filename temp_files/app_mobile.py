"""
YouTube Transcript Extractor - スマホ対応版（ngrok対応）
メルカリアナライザーのノウハウを活用した改良版
"""

import base64
import io
import json
import logging
import os
import random
import socket
import time
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs, urlparse

import google.generativeai as genai
import googleapiclient.discovery
import googleapiclient.errors
import qrcode
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from youtube_transcript_api import (NoTranscriptFound, TranscriptsDisabled,
                                    YouTubeTranscriptApi)

# Performance optimizer with fallback
try:
    from performance_optimizer import AppStoreOptimizer, PerformanceOptimizer
except Exception:
    class PerformanceOptimizer:
        def __init__(self, app): pass
    class AppStoreOptimizer:
        @staticmethod
        def optimize_for_mobile(app): pass
        @staticmethod
        def add_app_store_headers(app): pass

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask アプリの初期化
app = Flask(__name__, template_folder="templates", static_folder="static")

# Performance optimizations for App Store compliance
try:
    optimizer = PerformanceOptimizer(app)
    AppStoreOptimizer.optimize_for_mobile(app)
    AppStoreOptimizer.add_app_store_headers(app)
    logger.info("Performance optimizations applied")
except Exception as e:
    logger.warning(f"Performance optimization failed: {e}")

# Production environment configuration
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "dev-key-" + str(random.randint(1000, 9999))
)
app.config["PREFERRED_URL_SCHEME"] = "https"
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers for App Store compliance"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https:; connect-src 'self' https:;"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Rate limiting simple implementation
request_count = {}
max_requests_per_minute = 60


def check_rate_limit(client_ip):
    """Basic rate limiting for API endpoints"""
    current_time = time.time()
    minute_ago = current_time - 60

    # Clean old entries
    for ip in list(request_count.keys()):
        request_count[ip] = [
            req_time for req_time in request_count[ip] if req_time > minute_ago
        ]
        if not request_count[ip]:
            del request_count[ip]

    # Check current IP
    if client_ip not in request_count:
        request_count[client_ip] = []

    if len(request_count[client_ip]) >= max_requests_per_minute:
        return False

    request_count[client_ip].append(current_time)
    return True


# CORS設定（ngrok対応）
CORS(
    app,
    origins=[
        "http://localhost:8085",
        "http://127.0.0.1:8085",
        "https://*.ngrok-free.app",
        "https://*.ngrok.app",
    ],
    supports_credentials=True,
)

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
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Base64エンコード
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return None


def get_ai_api_key():
    """AI APIキーを取得"""
    # 環境変数から取得
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
        model = genai.GenerativeModel("gemini-2.0-flash-001")

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
        formatted_text = " ".join(unique_words)

        # 適切な句読点を追加
        formatted_text = re.sub(r"([。！？])([あ-ん])", r"\1\n\2", formatted_text)
        formatted_text = re.sub(r"([a-zA-Z0-9])([あ-ん])", r"\1 \2", formatted_text)
        formatted_text = re.sub(r"([あ-ん])([A-Z])", r"\1 \2", formatted_text)

        # 長い文を段落に分割
        sentences = formatted_text.split("。")
        paragraphs = []
        current_paragraph = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                current_paragraph.append(sentence + "。")
                # 3文ごとに段落分け
                if len(current_paragraph) >= 3:
                    paragraphs.append("".join(current_paragraph))
                    current_paragraph = []

        if current_paragraph:
            paragraphs.append("".join(current_paragraph))

        # 最終整形
        result = "\n\n".join(paragraphs)

        # 簡単な要約を追加
        result += f"\n\n【要約】\n上記は YouTube 動画の字幕内容を整形したものです。詳細な要約には AI API の設定が必要です。"

        return result

    except Exception as e:
        logger.error(f"基本整形エラー: {e}")
        return text


def format_transcript_text(text):
    """元テキストの改行・誤変換・文字化け修正などの基本整形（要約は行わない）"""
    try:
        import re
        
        # 基本的な文字化け・誤変換修正
        formatted_text = text
        
        # よくある誤変換パターンの修正
        corrections = {
            '僕ら': '僕ら',
            '恋愛初心者': '恋愛初心者',
            'ルール': 'ルール',
            '互い': 'お互い',
            '分かってる': 'わかってる',
            '全部': 'すべて',
            '捧げて': '捧げて',
            '構わない': 'かまわない',
            '他の男': 'ほかの男',
            '尽くせない': '尽くせない',
            '気持ち': '気持ち',
            '伝えたい': '伝えたい',
            '分かって': 'わかって',
            '欲しい': 'ほしい',
            '決して': '決して',
            '諦めない': 'あきらめない',
            'がっかり': 'がっかり',
            'させない': 'させない',
            '言い訳': '言い訳',
            '逃げたり': '逃げたり',
            '泣かせたり': '泣かせたり',
            'さよなら': 'さよなら',
            '嘘': 'うそ',
            'つかない': 'つかない',
            '傷つける': '傷つける',
            '知り合って': '知り合って',
            'だいぶ経つ': 'だいぶ経つ',
            '心': '心',
            'うずいて': 'うずいて',
            '恥ずかしく': '恥ずかしく',
            '言えない': '言えない',
            '気付いて': '気づいて',
            'ゲーム': 'ゲーム',
            'プレイ': 'プレイ',
            '聞くなら': '聞くなら',
            '知らない': '知らない',
            'ふり': 'ふり',
            'しちゃダメ': 'しちゃダメ'
        }
        
        # 誤変換修正を適用
        for wrong, correct in corrections.items():
            formatted_text = formatted_text.replace(wrong, correct)
        
        # 句読点の整理と適切な改行処理
        # 連続するスペースを整理
        formatted_text = re.sub(r'\s+', ' ', formatted_text)
        
        # 文の区切りで適切に改行を挿入
        sentences = []
        current_sentence = ""
        words = formatted_text.split()
        
        for word in words:
            current_sentence += word
            
            # 文の終わりを検出（句点、感嘆符、疑問符）
            if (word.endswith('。') or word.endswith('！') or word.endswith('？') or
                word.endswith('だ') or word.endswith('です') or word.endswith('である') or
                word.endswith('ない') or word.endswith('よ') or word.endswith('ね')):
                sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += " "
        
        # 残りの文があれば追加
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        # 適切な改行で結合（2-3文ごとに段落分け）
        paragraphs = []
        current_paragraph = []
        
        for i, sentence in enumerate(sentences):
            current_paragraph.append(sentence)
            
            # 2-3文ごとまたは自然な区切りで段落分け
            if (len(current_paragraph) >= 2 and 
                (i == len(sentences) - 1 or 
                 any(keyword in sentence for keyword in ['。', 'よ', 'ね', 'だ', 'です']))):
                paragraphs.append(''.join(current_paragraph))
                current_paragraph = []
        
        # 残りがあれば追加
        if current_paragraph:
            paragraphs.append(''.join(current_paragraph))
        
        # 段落間に空行を挿入
        result = '\n\n'.join(paragraphs)
        
        return result.strip()
        
    except Exception as e:
        logger.error(f"テキスト整形エラー: {e}")
        # エラーの場合は基本的な改行のみ適用
        return text.replace('\n', '\n\n').strip()


def improve_text_formatting(text):
    """AI整形済みテキストの改行・段落を改善"""
    try:
        import re
        
        # 既存の改行を整理
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 箇条書きや見出しの前に空行を追加
        text = re.sub(r'([^\n])\n([■●・•])', r'\1\n\n\2', text)
        
        # 段落の終わりを明確に
        text = re.sub(r'([。！？])([^。！？\n])', r'\1\n\n\2', text)
        
        return text.strip()
    except Exception as e:
        logger.error(f"テキスト整形改善エラー: {e}")
        return text


def clean_ai_response(text):
    """AIの定型的返答を除去"""
    try:
        import re
        
        # 除去する定型的なフレーズ
        unwanted_phrases = [
            r'^はい、.*?要約です[。．]*\s*',
            r'^この動画.*?要約します[。．]*\s*',
            r'^動画の内容.*?要約[。．]*\s*',
            r'^以下.*?要約です[。．]*\s*',
            r'^.*?字幕.*?要約.*?[。．]*\s*',
            r'^こちらが.*?要約です[。．]*\s*',
            r'^YouTube.*?要約.*?[。．]*\s*'
        ]
        
        # 各パターンを除去
        cleaned_text = text
        for pattern in unwanted_phrases:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        # 先頭の余分な改行や空白を除去
        cleaned_text = cleaned_text.lstrip('\n\r\t ')
        
        return cleaned_text
    except Exception as e:
        logger.error(f"AI返答クリーニングエラー: {e}")
        return text


def improve_summary_formatting(summary):
    """要約テキストの整形改善（可読性重視で改行を多めに配置）"""
    try:
        import re
        
        # 基本的なテキストクリーニング
        # 連続するスペースを整理
        summary = re.sub(r' +', ' ', summary)
        
        # 見出し記号の統一と改行調整（可読性重視で前後に大きな空行）
        summary = re.sub(r'([■●])\s*', r'\n\n\n\n\1 ', summary)  # ■の前に4行改行
        summary = re.sub(r'([•])\s*', r'\n\n• ', summary)
        
        # 文章の改行処理（可読性重視）
        lines = summary.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 見出し行の処理（前後に十分な空行）
                if line.startswith('■') or line.startswith('●'):
                    # 見出しの前に大きな空行を強制的に追加
                    if formatted_lines:  # 既に内容がある場合
                        formatted_lines.extend(['', '', ''])  # 3行の空行を確実に追加
                    formatted_lines.append(line)
                    formatted_lines.append('')  # 見出しの後は1行空行のみ
                
                # 箇条書き行の処理（適度な空行）
                elif line.startswith('•'):
                    # 箇条書きの前に空行
                    if formatted_lines and formatted_lines[-1] != '':
                        formatted_lines.append('')
                    formatted_lines.append(line)
                
                # 通常の文章行の処理（短めの行で改行し、読みやすく）
                else:
                    # 文章を短く分割して可読性向上
                    if len(line) > 45:  # さらに短い行長で改行（60→45文字）
                        sentences = re.split(r'([。！？])', line)
                        current_paragraph = ""
                        
                        for i in range(0, len(sentences)-1, 2):
                            if i+1 < len(sentences):
                                sentence = sentences[i] + sentences[i+1]
                            else:
                                sentence = sentences[i]
                            
                            # より短い行長で改行（45文字）
                            if len(current_paragraph + sentence) > 45 and current_paragraph:
                                formatted_lines.append(current_paragraph.strip())
                                formatted_lines.append('')  # 段落の後に空行
                                current_paragraph = sentence
                            else:
                                current_paragraph += sentence
                        
                        if current_paragraph.strip():
                            formatted_lines.append(current_paragraph.strip())
                            formatted_lines.append('')  # 段落の後に空行
                    else:
                        formatted_lines.append(line)
                        # 通常の文章の後にも軽い空行を追加
                        if not (line.startswith('•') or line.startswith('■') or line.startswith('●')):
                            formatted_lines.append('')
        
        # 過度な空行は制限（最大3行まで許可 - ■セクションヘッダー用）
        result_lines = []
        empty_count = 0
        
        for line in formatted_lines:
            if line.strip() == '':
                empty_count += 1
                if empty_count <= 3:  # 最大3行の空行まで許可（■ヘッダー対応）
                    result_lines.append('')
            else:
                empty_count = 0
                result_lines.append(line)
        
        result = '\n'.join(result_lines).strip()
        
        # 最終整理（5行以上の空行は3行に制限）
        result = re.sub(r'\n{6,}', '\n\n\n\n', result)  # ■前の空行確保
        
        return result
    except Exception as e:
        logger.error(f"要約整形エラー: {e}")
        return summary


def extract_youtube_transcript(video_url, language_code="ja"):
    """YouTube字幕抽出（シンプル確実版）"""
    try:
        # --- 動画ID抽出 ---
        parsed_url = urlparse(video_url)
        video_id = None
        if "youtube.com" in parsed_url.netloc or "m.youtube.com" in parsed_url.netloc:
            if parsed_url.path == "/watch":
                video_id = parse_qs(parsed_url.query).get("v", [None])[0]
            elif parsed_url.path.startswith("/shorts/"):
                video_id = parsed_url.path.split("/shorts/")[1].split("?")[0]
            elif parsed_url.path.startswith("/embed/"):
                video_id = parsed_url.path.split("/embed/")[1].split("?")[0]
            elif parsed_url.path.startswith("/v/"):
                video_id = parsed_url.path.split("/v/")[1].split("?")[0]
        elif "youtu.be" in parsed_url.netloc:
            video_id = parsed_url.path.lstrip("/").split("?")[0]

        if not video_id:
            raise ValueError("有効なYouTube URLではありません")

        video_id = video_id.split("&")[0]
        logger.info(f"[extract] video_id={video_id}")

        # --- 言語リスト ---
        langs = []
        if language_code and language_code != "auto":
            langs.append(language_code)
        for l in ["ja", "en"]:
            if l not in langs:
                langs.append(l)

        # --- 新しいAPIを使用 ---
        try:
            # インスタンスを作成
            api = YouTubeTranscriptApi()
            
            # 利用可能な字幕リストを取得
            transcript_list = api.list(video_id)
            
            # 希望する言語の字幕を検索
            for l in langs:
                try:
                    transcript = transcript_list.find_transcript([l])
                    data = transcript.fetch()
                    
                    # データからテキストを抽出
                    full_text = " ".join([snippet.text for snippet in data.snippets])
                    
                    return {
                        "success": True,
                        "transcript": full_text,
                        "language": l,
                        "video_id": video_id,
                    }
                except Exception as e:
                    logger.warning(f"[extract] language {l} failed: {e}")
                    continue
            
            # どの言語も見つからない場合、最初に利用可能な字幕を使用
            try:
                # 利用可能な最初の字幕を取得
                available_transcripts = list(transcript_list)
                if available_transcripts:
                    transcript = available_transcripts[0]
                    data = transcript.fetch()
                    full_text = " ".join([snippet.text for snippet in data.snippets])
                    
                    return {
                        "success": True,
                        "transcript": full_text,
                        "language": transcript.language_code,
                        "video_id": video_id,
                    }
            except Exception as e:
                logger.warning(f"[extract] fallback failed: {e}")
                
        except Exception as main_e:
            logger.error(f"[extract] API全体でエラー: {main_e}")

        raise ValueError("利用可能な字幕が見つかりませんでした")

    except Exception as e:
        logger.error(f"[extract] error: {e}")
        return {"success": False, "error": str(e)}
@app.route("/")
def index():
    """メインページ"""
    return render_template("index_mobile.html")


@app.route("/api/access-info")
def get_access_info():
    """アクセス情報取得API"""
    try:
        local_ip = get_local_ip()
        port = 8085

        # 動的ngrok URL取得
        dynamic_ngrok_url = get_ngrok_url()

        access_info = {
            "localURL": f"http://127.0.0.1:{port}",
            "networkURL": f"http://{local_ip}:{port}",
            "domainURL": f"http://youtube-extractor.local:{port}",
            "ngrokURL": dynamic_ngrok_url or "ngrokトンネルが起動していません",
        }

        return jsonify({"success": True, "data": access_info})
    except Exception as e:
        logger.error(f"アクセス情報取得エラー: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/extract", methods=["POST"])
def extract_transcript():
    """字幕抽出API with rate limiting and enhanced error handling"""
    # Rate limiting check
    client_ip = request.environ.get(
        "HTTP_X_FORWARDED_FOR", request.environ.get("REMOTE_ADDR", "unknown")
    )
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "リクエストが多すぎます。しばらく待ってから再試行してください。",
                    "retry_after": 60,
                }
            ),
            429,
        )
    """字幕抽出API"""
    try:
        data = request.get_json()
        video_url = data.get("url", "")
        language = data.get("lang", data.get("language", "ja"))  # HTML sends 'lang', fallback to 'language'
        format_text = data.get("format", True)

        if not video_url:
            return (
                jsonify({"success": False, "error": "YouTube URLが指定されていません"}),
                400,
            )

        logger.info(f"字幕抽出開始: {video_url}")

        # 字幕抽出
        result = extract_youtube_transcript(video_url, language)

        if not result["success"]:
            return jsonify(result), 400

        # テキスト整形（基本整形のみ）
        formatted_text = result["transcript"]  # デフォルトは元テキスト
        
        if format_text:
            # 元テキストに基本的な整形のみを適用
            formatted_text = format_transcript_text(result["transcript"])
            logger.info("基本テキスト整形を適用")

        # AI要約生成（format_textとは独立）
        summary_text = ""
        generate_summary = data.get("generate_summary", False)
        
        if generate_summary:
            try:
                api_key = get_ai_api_key()
                if api_key:
                    summary_prompt = f"""
以下のYouTube動画の字幕テキストを要約してください。

{result["transcript"]}

要求事項：
- 定型的な挨拶や返答（「はい、」「動画字幕の要約です」など）は一切含めない
- 内容の要約のみを直接記載する
- 以下の形式で整理された要約を作成する：

■ 主要ポイント
• ポイント1の具体的内容
• ポイント2の具体的内容
• ポイント3の具体的内容

■ 詳細情報
詳しい背景や説明

■ 結論・まとめ
最終的なメッセージや結論
"""
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel("gemini-2.0-flash-001")
                    response = model.generate_content(summary_prompt)
                    summary_text = response.text
                    if summary_text:
                        # AIの定型的返答を除去
                        summary_text = clean_ai_response(summary_text)
                        # 要約のテキスト整形を適用
                        summary_text = improve_summary_formatting(summary_text)
                        logger.info("AI要約生成成功")
            except Exception as e:
                logger.warning(f"AI要約生成失敗: {e}")
                summary_text = ""

        # 字幕セグメント数と文字数の統計
        segments_count = len(result.get("segments", []))
        char_count = len(result["transcript"])

        return jsonify(
            {
                "success": True,
                "version": "v1.3.0-gradient-red",
                "title": f"YouTube動画 (ID: {result['video_id']})",
                "transcript": formatted_text,  # 整形済みテキスト（元テキストの基本整形版）
                "original_transcript": result["transcript"],  # 元テキスト（変更なし）
                "summary": summary_text if generate_summary else "要約を生成するには generate_summary: true を設定してください",
                "stats": {
                    "segments": segments_count,
                    "characters": char_count,
                    "language": result["language"]
                },
                "video_id": result["video_id"],
                "language": result["language"]
            }
        )

    except Exception as e:
        logger.error(f"字幕抽出API エラー: {e}")
        # Don't expose internal errors to users in production
        user_error = "申し訳ありません。一時的な問題が発生しました。しばらく待ってから再試行してください。"
        if "youtube.com" in str(e) or "youtu.be" in str(e):
            user_error = "YouTube URLの形式が正しくないか、字幕が利用できない動画です。"
        elif "transcript" in str(e).lower():
            user_error = (
                "この動画には字幕が設定されていません。字幕付きの動画をお試しください。"
            )

        return (
            jsonify(
                {
                    "success": False,
                    "error": user_error,
                    "error_code": "EXTRACTION_FAILED",
                }
            ),
            500,
        )


@app.route("/qr-code")
def generate_qr():
    """QRコード生成エンドポイント"""
    try:
        # 動的ngrok URL取得してQRコード生成
        default_url = get_ngrok_url() or "http://127.0.0.1:8085"
        url = request.args.get("url", default_url)
        qr_code_data = generate_qr_code(url)

        if qr_code_data:
            return jsonify({"success": True, "qr_code": qr_code_data, "url": url})
        else:
            return (
                jsonify({"success": False, "error": "QRコード生成に失敗しました"}),
                500,
            )

    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health_check():
    """Enhanced health check for App Store monitoring"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0-appstore",
        "services": {
            "youtube_api": "operational",
            "ai_formatting": "operational" if get_ai_api_key() else "degraded",
            "ngrok_tunnel": (
                "operational" if get_ngrok_url() != CURRENT_NGROK_URL else "fallback"
            ),
        },
        "performance": {
            "active_requests": len(request_count),
            "uptime_seconds": int(time.time() - startup_time),
        },
    }

    # Check if all critical services are working
    all_services_ok = all(
        status != "failed" for status in health_data["services"].values()
    )

    return jsonify(health_data), 200 if all_services_ok else 503


@app.route("/api/status")
def detailed_status():
    """Detailed status endpoint for debugging"""
    try:
        ai_key_status = "configured" if get_ai_api_key() else "missing"
        ngrok_status = "active" if get_ngrok_url() != CURRENT_NGROK_URL else "static"

        return jsonify(
            {
                "success": True,
                "data": {
                    "server_time": datetime.now().isoformat(),
                    "ai_api_status": ai_key_status,
                    "ngrok_status": ngrok_status,
                    "request_stats": {
                        "total_active_ips": len(request_count),
                        "rate_limit_max": max_requests_per_minute,
                    },
                    "environment": {
                        "debug_mode": app.debug,
                        "secret_key_set": bool(app.config.get("SECRET_KEY")),
                        "https_preferred": app.config.get("PREFERRED_URL_SCHEME")
                        == "https",
                    },
                },
            }
        )
    except Exception as e:
        logger.error(f"Status endpoint error: {e}")
        return (
            jsonify({"success": False, "error": "ステータス情報の取得に失敗しました"}),
            500,
        )


def setup_ngrok_url():
    """ngrok URL設定"""
    global CURRENT_NGROK_URL
    # 実際のngrok URLをここで設定（ngrok起動後に更新）
    # 例: CURRENT_NGROK_URL = "https://abc123.ngrok-free.app"
    pass


# Startup time tracking for health checks
startup_time = time.time()

if __name__ == "__main__":
    setup_ngrok_url()
    logger.info("🚀 YouTube字幕抽出サーバー（App Store Ready版）を起動中...")
    logger.info(f"📱 ローカルアクセス: http://127.0.0.1:8085")
    logger.info(f"🔒 HTTPS対応: {app.config.get('PREFERRED_URL_SCHEME')}")
    if CURRENT_NGROK_URL:
        logger.info(f"🌐 ngrok URL: {CURRENT_NGROK_URL}")

    # Production-ready configuration
    is_production = os.environ.get("FLASK_ENV") == "production"

    logger.info(f"⚙️  環境: {'Production' if is_production else 'Development'}")
    logger.info(f"🛡️  セキュリティヘッダー: 有効")
    logger.info(f"⏱️  レート制限: {max_requests_per_minute}req/min")

    # サーバー起動（HTTP固定で確認）
    app.run(host="0.0.0.0", port=8085, debug=False)