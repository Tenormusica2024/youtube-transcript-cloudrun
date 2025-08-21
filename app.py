"""
YouTube Transcript Extractor - Cloud Run版
ポート干渉を避け、固定URLで動作するバージョン
"""

import json
import logging
import os
import random
import socket
import time
from datetime import datetime
from functools import wraps
from urllib.parse import parse_qs, urlparse
import uuid
import shutil

import google.generativeai as genai
import googleapiclient.discovery
import googleapiclient.errors
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from youtube_transcript_api import (NoTranscriptFound, TranscriptsDisabled,
                                    YouTubeTranscriptApi)

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# 環境変数検証を統合
def validate_environment_on_startup():
    """起動時環境変数検証"""
    try:
        import importlib.util

        env_validator_path = os.path.join(os.path.dirname(__file__), "env_validator.py")

        if os.path.exists(env_validator_path):
            spec = importlib.util.spec_from_file_location(
                "env_validator", env_validator_path
            )
            env_validator = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(env_validator)

            validator = env_validator.EnvValidator()
            is_valid = validator.validate_all()

            if not is_valid:
                logger.warning(
                    "⚠️  環境変数に問題が検出されました - 自動修正を試行中..."
                )
                validator.auto_fix_env_file()

                # 修正後の再検証
                validator_recheck = env_validator.EnvValidator()
                validator_recheck.validate_all()
                logger.info("✅ 環境変数修正完了 - サービス開始")
            else:
                logger.info("✅ 全ての環境変数が正常に設定されています")
        else:
            logger.warning("env_validator.py not found - skipping validation")

    except Exception as e:
        logger.warning(f"Environment validation failed: {e}")


# Flask アプリケーション設定
app = Flask(__name__, template_folder="templates", static_folder="static")

# CORS設定（環境変数から許可オリジンを取得）
cors_origins = os.environ.get("CORS_ORIGINS", "https://*.run.app").split(",")
cors_origins = [origin.strip() for origin in cors_origins]
CORS(app, origins=cors_origins, allow_headers=["Content-Type", "Authorization"])

# 環境変数読み込み
load_dotenv()

# Cloud Run用ポート設定（環境変数PORTを優先）
PORT = int(os.environ.get("PORT", 8080))


# APIキー取得（環境変数を優先）
def get_youtube_api_key():
    """YouTube API キーを取得"""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        # .envファイルから取得を試みる
        api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logger.error("YouTube API key not found in environment variables")
        raise ValueError(
            "YouTube APIキーが設定されていません。環境変数YOUTUBE_API_KEYを設定してください。"
        )

    return api_key


def get_gemini_api_key():
    """Gemini API キーを取得"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # .envファイルから取得を試みる
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.error("Gemini API key not found in environment variables")
        raise ValueError(
            "Gemini APIキーが設定されていません。環境変数GEMINI_API_KEYを設定してください。"
        )

    return api_key


def get_transcript_api_token():
    """Transcript API トークンを取得"""
    token = os.environ.get("TRANSCRIPT_API_TOKEN")
    if not token:
        # .envファイルから取得を試みる
        token = os.getenv("TRANSCRIPT_API_TOKEN")

    if not token:
        logger.error("Transcript API token not found in environment variables")
        raise ValueError(
            "Transcript APIトークンが設定されていません。環境変数TRANSCRIPT_API_TOKENを設定してください。"
        )

    return token


def require_auth(f):
    """認証が必要なエンドポイント用デコレータ"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        logger.info(f"Received auth header: {repr(auth_header)}")

        if not auth_header:
            logger.warning("No authorization header provided")
            return jsonify({"error": "Authorization header required"}), 401

        try:
            parts = auth_header.split(" ", 1)
            logger.info(f"Auth header split into {len(parts)} parts: {parts}")

            if len(parts) != 2:
                logger.warning(
                    f"Invalid authorization header format: expected 2 parts, got {len(parts)}"
                )
                return jsonify({"error": "Invalid Authorization header format"}), 401

            scheme, token = parts
            logger.info(f"Scheme: {repr(scheme)}, Token: {repr(token[:10])}...")

            if scheme.lower() != "bearer":
                logger.warning(f"Invalid scheme: expected 'bearer', got {repr(scheme)}")
                return jsonify({"error": "Bearer token required"}), 401

            expected_token = get_transcript_api_token()
            logger.info(
                f"Expected token: {repr(expected_token[:10] if expected_token else None)}..."
            )

            if token != expected_token:
                logger.warning(
                    f"Token mismatch: got {repr(token[:10])}..., expected {repr(expected_token[:10] if expected_token else None)}..."
                )
                return jsonify({"error": "Invalid token"}), 401

            logger.info("Authorization successful")

        except ValueError as ve:
            logger.error(f"ValueError in auth: {ve}")
            return jsonify({"error": "Invalid Authorization header format"}), 401
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({"error": "Authentication failed"}), 401

        return f(*args, **kwargs)

    return decorated_function


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
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API client initialized successfully")
    gemini_client = genai
except Exception as e:
    logger.error(f"Failed to initialize Gemini API client: {e}")
    gemini_client = None

# プロキシ機能は一時的に無効化（接続エラーを避けるため）
FREE_PROXIES = []


def get_working_proxy():
    """動作するプロキシを検索（現在は無効化）"""
    logger.info("Proxy search disabled for debugging")
    return None


def create_transcript_session_with_proxy():
    """プロキシ付きセッションを作成"""
    session = requests.Session()

    # プロキシを試行
    proxy = get_working_proxy()
    if proxy:
        session.proxies.update(proxy)
        logger.info("Using proxy for transcript request")

    # User-Agentをランダム化
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    ]

    session.headers.update(
        {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    )

    return session


def get_video_id(url):
    """YouTube URLから動画IDを抽出（YouTube Shorts対応）"""
    try:
        parsed_url = urlparse(url)

        # youtu.be形式
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:].split("?")[0].split("&")[0]

        # youtube.com形式
        if parsed_url.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            # 通常の動画 (/watch?v=VIDEO_ID)
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                return params.get("v", [None])[0]
            # YouTube Shorts (/shorts/VIDEO_ID)
            elif parsed_url.path.startswith("/shorts/"):
                video_id = (
                    parsed_url.path.split("/shorts/")[1].split("?")[0].split("&")[0]
                )
                logger.info(f"YouTube Shorts動画を検出: {video_id}")
                return video_id
            # Embed形式 (/embed/VIDEO_ID)
            elif parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2].split("?")[0].split("&")[0]
            # その他のパス形式 (/v/VIDEO_ID)
            elif parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2].split("?")[0].split("&")[0]

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

        if "items" in response and len(response["items"]) > 0:
            title = response["items"][0]["snippet"]["title"]
            logger.info(f"Retrieved title for video {video_id}: {title}")
            return title
        else:
            logger.warning(f"No title found for video {video_id}")
            return "タイトルを取得できませんでした"
    except Exception as e:
        logger.error(f"Error getting video title for {video_id}: {e}")
        return "タイトル取得エラー"


def get_transcript(video_id, lang="ja"):
    """字幕を取得（プロキシ付きで試行）"""
    try:
        logger.info(
            f"Attempting to get transcript for video {video_id} in language {lang}"
        )

        # 複数の戦略で試行
        strategies = [
            ("proxy_session", "プロキシ付きセッション"),
            ("stealth_session", "ステルスセッション"),
            ("minimal_session", "ミニマルセッション"),
        ]

        for strategy, description in strategies:
            try:
                logger.info(f"Trying {description} for video {video_id}")

                if strategy == "proxy_session":
                    session = create_transcript_session_with_proxy()
                elif strategy == "stealth_session":
                    session = requests.Session()
                    session.headers.update(
                        {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept": "*/*",
                            "Accept-Language": "en-US,en;q=0.5",
                            "Connection": "keep-alive",
                        }
                    )
                else:  # minimal_session
                    session = requests.Session()
                    session.headers.update(
                        {"User-Agent": "YouTube Transcript API 1.2.2"}
                    )

                # レート制限対策
                delay = random.uniform(3, 8)
                logger.info(f"Waiting {delay:.1f} seconds before request...")
                time.sleep(delay)

                # APIインスタンスを作成して試行（http_clientパラメータを使用）
                try:
                    api = YouTubeTranscriptApi(http_client=session)
                    logger.info(f"Created API instance for {description}")
                    fetched_transcript = api.fetch(video_id, languages=[lang])
                    logger.info(f"Fetched transcript for {description}")
                    transcript = fetched_transcript.to_raw_data()
                    logger.info(f"Converted to raw data for {description}")
                except Exception as api_error:
                    logger.error(f"API error in {description}: {api_error}")
                    raise api_error

                logger.info(
                    f"Success with {description}! Found {len(transcript)} segments"
                )
                return transcript

            except Exception as strategy_error:
                logger.warning(f"{description} failed: {str(strategy_error)}")
                continue

        # 英語でも同じ戦略を試行
        for strategy, description in strategies:
            try:
                logger.info(f"Trying {description} for English transcript")

                if strategy == "proxy_session":
                    session = create_transcript_session_with_proxy()
                elif strategy == "stealth_session":
                    session = requests.Session()
                    session.headers.update(
                        {
                            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                            "Accept": "*/*",
                            "Accept-Language": "en-US,en;q=0.9",
                        }
                    )
                else:  # minimal_session
                    session = requests.Session()

                time.sleep(random.uniform(4, 9))
                api = YouTubeTranscriptApi(http_client=session)
                fetched_transcript = api.fetch(video_id, languages=["en"])
                transcript = fetched_transcript.to_raw_data()

                logger.info(
                    f"English success with {description}! Found {len(transcript)} segments"
                )
                return transcript

            except Exception as en_error:
                logger.warning(f"English {description} failed: {str(en_error)}")
                continue

        # 最後の試行：auto言語検出
        try:
            logger.info("Final attempt with auto language detection...")
            time.sleep(random.uniform(5, 12))

            session = requests.Session()
            session.headers.update({"User-Agent": "youtube-transcript-extractor/1.0"})

            api = YouTubeTranscriptApi(http_client=session)
            fetched_transcript = api.fetch(video_id, languages=["auto", "en", lang])
            transcript = fetched_transcript.to_raw_data()

            logger.info(f"Auto detection success! Found {len(transcript)} segments")
            return transcript

        except Exception as auto_error:
            logger.error(f"All methods failed for video {video_id}: {auto_error}")

    except NoTranscriptFound:
        error_msg = "この動画には字幕が存在しないか、利用できません。"
        logger.warning(f"No transcript available for video {video_id}")
        raise ValueError(error_msg)
    except TranscriptsDisabled:
        error_msg = "この動画の字幕は無効化されています。"
        logger.warning(f"Transcripts disabled for video {video_id}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"字幕の取得に失敗しました: {str(e)}"
        logger.error(f"Final error for video {video_id}: {e}")
        raise ValueError(error_msg)


def format_transcript(transcript, format_type="txt"):
    """字幕をフォーマット"""
    if format_type == "json":
        return json.dumps(transcript, ensure_ascii=False, indent=2)
    elif format_type == "srt":
        # SRT形式（タイムスタンプ付き）
        srt_content = []
        for i, item in enumerate(transcript, 1):
            start = format_timestamp(item["start"])
            end = format_timestamp(item["start"] + item["duration"])
            srt_content.append(f"{i}\n{start} --> {end}\n{item['text']}\n")
        return "\n".join(srt_content)
    else:
        # デフォルト: プレーンテキスト（スペースで結合して自然な文章に）
        return " ".join([item["text"] for item in transcript])


def format_timestamp(seconds):
    """秒数をSRTタイムスタンプ形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")


def load_prompt_from_file(prompt_file, text):
    """外部ファイルからプロンプトを読み込み、テキストを置換"""
    try:
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)
        
        if not os.path.exists(prompt_path):
            logger.warning(f"Prompt file not found: {prompt_path}")
            return None
            
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        return prompt_template.format(text=text)
    except Exception as e:
        logger.error(f"Error loading prompt from {prompt_file}: {e}")
        return None

def format_text_with_gemini(text):
    """Gemini AIを使用してテキストを可読性良く整形"""
    if not gemini_client:
        logger.warning("Gemini client not initialized, returning original text")
        return text

    try:
        # 外部ファイルからプロンプトを読み込み
        prompt = load_prompt_from_file("format_prompt.txt", text)
        
        if not prompt:
            # フォールバック用の基本プロンプト
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

        model = gemini_client.GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=2000,
            ),
        )

        formatted_text = response.text.strip()
        logger.info("Text formatted successfully using Gemini")
        return formatted_text

    except Exception as e:
        logger.error(f"Error formatting text with Gemini: {e}")
        return text


def save_to_archive(video_id, title, original_text, formatted_text, summary, url=None):
    """要約結果をアーカイブに保存"""
    try:
        archive_dir = os.path.join(os.path.dirname(__file__), "archive")
        os.makedirs(archive_dir, exist_ok=True)
        
        # ユニークなファイル名を生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{video_id}_{unique_id}.json"
        
        archive_data = {
            "id": unique_id,
            "timestamp": datetime.now().isoformat(),
            "video_id": video_id,
            "title": title,
            "url": url,
            "original_text": original_text,
            "formatted_text": formatted_text,
            "summary": summary,
            "stats": {
                "original_length": len(original_text),
                "formatted_length": len(formatted_text),
                "summary_length": len(summary)
            }
        }
        
        archive_path = os.path.join(archive_dir, filename)
        with open(archive_path, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Archive saved: {filename}")
        return unique_id
        
    except Exception as e:
        logger.error(f"Error saving to archive: {e}")
        return None

def get_archive_list(limit=50, offset=0):
    """アーカイブリストを取得"""
    try:
        archive_dir = os.path.join(os.path.dirname(__file__), "archive")
        if not os.path.exists(archive_dir):
            return {"archives": [], "total": 0}
        
        # ファイル一覧を取得してソート
        archive_files = []
        for filename in os.listdir(archive_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(archive_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    archive_files.append({
                        "filename": filename,
                        "id": data.get("id", "unknown"),
                        "timestamp": data.get("timestamp", ""),
                        "video_id": data.get("video_id", ""),
                        "title": data.get("title", ""),
                        "url": data.get("url", ""),
                        "summary_preview": data.get("summary", "")[:100] + "..." if len(data.get("summary", "")) > 100 else data.get("summary", ""),
                        "stats": data.get("stats", {})
                    })
                except Exception as e:
                    logger.warning(f"Error reading archive file {filename}: {e}")
                    continue
        
        # タイムスタンプでソート（新しい順）
        archive_files.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # ページング
        total = len(archive_files)
        paginated_files = archive_files[offset:offset + limit]
        
        return {
            "archives": paginated_files,
            "total": total,
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting archive list: {e}")
        return {"archives": [], "total": 0}

def get_archive_by_id(archive_id):
    """IDでアーカイブを取得"""
    try:
        archive_dir = os.path.join(os.path.dirname(__file__), "archive")
        
        for filename in os.listdir(archive_dir):
            if filename.endswith('.json') and archive_id in filename:
                filepath = os.path.join(archive_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting archive by ID {archive_id}: {e}")
        return None

def summarize_with_gemini(text):
    """Gemini AIを使用してテキストを要約"""
    if not gemini_client:
        logger.warning("Gemini client not initialized, returning empty summary")
        return ""

    try:
        # 外部ファイルからプロンプトを読み込み
        summary_prompt = load_prompt_from_file("summary_prompt.txt", text)
        
        if not summary_prompt:
            # フォールバック用の基本プロンプト
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

        model = gemini_client.GenerativeModel("gemini-2.0-flash-001")
        response = model.generate_content(
            summary_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=1200,
            ),
        )

        summary = response.text.strip()
        logger.info("Text summarized successfully using Gemini")
        return summary

    except Exception as e:
        logger.error(f"Error summarizing text with Gemini: {e}")
        return ""


@app.route("/")
def index():
    """メインページ"""
    return render_template("index.html")


@app.route("/health")
def health():
    """ヘルスチェックエンドポイント（Cloud Run用）"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "youtube_api": "configured" if youtube else "not configured",
        "gemini_api": "configured" if gemini_client else "not configured",
    }

    # 環境変数の健全性チェック
    env_issues = []
    try:
        get_transcript_api_token()
        health_status["auth_token"] = "configured"
    except ValueError:
        health_status["auth_token"] = "not configured"
        env_issues.append("TRANSCRIPT_API_TOKEN missing")

    try:
        get_youtube_api_key()
        health_status["youtube_api_key"] = "configured"
    except ValueError:
        health_status["youtube_api_key"] = "not configured"
        env_issues.append("YOUTUBE_API_KEY missing")

    try:
        get_gemini_api_key()
        health_status["gemini_api_key"] = "configured"
    except ValueError:
        health_status["gemini_api_key"] = "not configured"
        env_issues.append("GEMINI_API_KEY missing")

    if env_issues:
        health_status["status"] = "degraded"
        health_status["issues"] = env_issues
        return jsonify(health_status), 503

    return jsonify(health_status)


@app.route("/extract", methods=["POST"])
@require_auth
def extract():
    """字幕抽出エンドポイント"""
    try:
        logger.info("Extract endpoint called")
        data = request.json
        logger.info(f"Request data: {data}")

        # ローカル抽出された字幕テキストを受信
        transcript_text = data.get("transcript_text")
        url = data.get("url")
        lang = data.get("lang", "ja")
        format_type = data.get("format", "txt")

        # Cloud Run環境でURL直接取得を禁止
        is_cloud_run = os.environ.get("K_SERVICE") is not None

        if transcript_text:
            # ローカル抽出されたテキストを処理
            logger.info(
                f"Processing locally extracted transcript ({len(transcript_text)} chars)"
            )

            # プレーンテキストの場合は自動でGemini AIで整形と要約
            formatted_transcript = transcript_text
            summary_text = ""

            if format_type == "txt" and gemini_client:
                try:
                    logger.info("Auto-formatting transcript with Gemini AI")
                    formatted_transcript = format_text_with_gemini(transcript_text)

                    logger.info("Auto-summarizing transcript with Gemini AI")
                    summary_text = summarize_with_gemini(formatted_transcript)
                except Exception as e:
                    logger.warning(
                        f"Auto-formatting/summarizing failed, using original text: {e}"
                    )

            # アーカイブに保存
            archive_id = save_to_archive(
                video_id="locally_extracted",
                title="ローカル抽出字幕", 
                original_text=transcript_text,
                formatted_text=formatted_transcript,
                summary=summary_text,
                url=url
            )

            response_data = {
                "success": True,
                "video_id": "locally_extracted",
                "title": "ローカル抽出字幕",
                "formatted_transcript": formatted_transcript,
                "original_transcript": transcript_text,
                "summary": summary_text,
                "archive_id": archive_id,
                "stats": {
                    "total_characters": len(transcript_text),
                    "language": lang,
                },
            }

            logger.info("Successfully processed locally extracted transcript")
            return jsonify(response_data)

        elif url:
            # URL直接取得（Cloud Run環境では禁止）
            if is_cloud_run:
                return (
                    jsonify(
                        {
                            "error": "Cloud環境ではURLからの直接取得は無効です。字幕テキストかSRTファイルを送信してください。",
                            "suggestion": "ローカルPCで字幕を抽出し、transcript_textパラメータで送信してください。",
                        }
                    ),
                    400,
                )

            logger.info(f"Processing URL: {url}, Lang: {lang}, Format: {format_type}")

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
            if format_type == "txt" and gemini_client:
                try:
                    logger.info("Auto-formatting transcript with Gemini AI")
                    formatted_transcript = format_text_with_gemini(formatted_transcript)

                    logger.info("Auto-summarizing transcript with Gemini AI")
                    summary_text = summarize_with_gemini(formatted_transcript)
                except Exception as e:
                    logger.warning(
                        f"Auto-formatting/summarizing failed, using original text: {e}"
                    )

            # アーカイブに保存
            original_transcript_text = " ".join([item["text"] for item in transcript])
            archive_id = save_to_archive(
                video_id=video_id,
                title=title,
                original_text=original_transcript_text,
                formatted_text=formatted_transcript,
                summary=summary_text,
                url=url
            )

            # 統計情報
            stats = {
                "total_segments": len(transcript),
                "total_duration": sum(item["duration"] for item in transcript),
                "language": lang,
            }

            response_data = {
                "success": True,
                "video_id": video_id,
                "title": title,
                "formatted_transcript": formatted_transcript,
                "original_transcript": " ".join([item["text"] for item in transcript]),
                "summary": summary_text,
                "archive_id": archive_id,
                "stats": stats,
            }

            logger.info(f"Successfully processed video {video_id}")
            return jsonify(response_data)

        else:
            return jsonify({"error": "URLまたはtranscript_textが必要です"}), 400

    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in extract endpoint: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return (
            jsonify(
                {"success": False, "error": f"予期しないエラーが発生しました: {str(e)}"}
            ),
            500,
        )


@app.route("/supported_languages/<video_id>")
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
            languages.append(
                {
                    "code": transcript.language_code,
                    "name": transcript.language,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                }
            )

        return jsonify({"success": True, "languages": languages})
    except Exception as e:
        logger.error(f"Error getting supported languages for {video_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/format_text", methods=["POST"])
def format_text():
    """テキスト整形エンドポイント"""
    try:
        data = request.json
        text = data.get("text")

        if not text:
            return jsonify({"error": "テキストが指定されていません"}), 400

        if not gemini_client:
            return jsonify({"error": "Gemini APIが利用できません"}), 503

        # Gemini AIでテキストを整形
        formatted_text = format_text_with_gemini(text)

        response_data = {
            "success": True,
            "original_text": text,
            "formatted_text": formatted_text,
        }

        logger.info("Text formatting completed successfully")
        return jsonify(response_data)

    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in format_text: {e}")
        return (
            jsonify({"success": False, "error": "予期しないエラーが発生しました"}),
            500,
        )


@app.errorhandler(404)
def not_found(e):
    """404エラーハンドラー"""
    return jsonify({"error": "エンドポイントが見つかりません"}), 404


@app.route("/archive")
def archive_list():
    """アーカイブリストを取得"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        archive_data = get_archive_list(limit=limit, offset=offset)
        return jsonify(archive_data)
        
    except ValueError as e:
        return jsonify({"error": f"無効なパラメータです: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in archive list endpoint: {e}")
        return jsonify({"error": "アーカイブリストの取得に失敗しました"}), 500

@app.route("/archive/<archive_id>")
def archive_detail(archive_id):
    """アーカイブの詳細を取得"""
    try:
        archive_data = get_archive_by_id(archive_id)
        
        if archive_data:
            return jsonify(archive_data)
        else:
            return jsonify({"error": "アーカイブが見つかりません"}), 404
            
    except Exception as e:
        logger.error(f"Error in archive detail endpoint: {e}")
        return jsonify({"error": "アーカイブの取得に失敗しました"}), 500

@app.route("/archive/<archive_id>", methods=["DELETE"])
def delete_archive(archive_id):
    """アーカイブを削除"""
    try:
        archive_dir = os.path.join(os.path.dirname(__file__), "archive")
        
        for filename in os.listdir(archive_dir):
            if filename.endswith('.json') and archive_id in filename:
                filepath = os.path.join(archive_dir, filename)
                os.remove(filepath)
                logger.info(f"Archive deleted: {filename}")
                return jsonify({"success": True, "message": "アーカイブを削除しました"})
        
        return jsonify({"error": "アーカイブが見つかりません"}), 404
        
    except Exception as e:
        logger.error(f"Error deleting archive {archive_id}: {e}")
        return jsonify({"error": "アーカイブの削除に失敗しました"}), 500

@app.errorhandler(500)
def server_error(e):
    """500エラーハンドラー"""
    logger.error(f"Server error: {e}")
    return jsonify({"error": "サーバーエラーが発生しました"}), 500


if __name__ == "__main__":
    # 起動時環境変数検証を実行
    logger.info(
        "🔍 Starting YouTube Transcript Extractor with environment validation..."
    )
    validate_environment_on_startup()

    # Cloud Run環境かローカル環境かを判定
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if is_cloud_run:
        logger.info(f"Starting Cloud Run server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=False)
    else:
        # ローカル開発環境
        logger.info(f"Starting local development server on port {PORT}")
        app.run(host="127.0.0.1", port=PORT, debug=True)
