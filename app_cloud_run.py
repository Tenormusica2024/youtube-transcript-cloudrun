"""
YouTube Transcript Extractor - Cloud Run版
ポート干渉を避け、固定URLで動作するバージョン
"""

import json
import logging
import os
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import googleapiclient.discovery
import googleapiclient.errors
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

# Flask アプリケーション設定
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Cloud Runでのクロスオリジン対応

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
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]

        # youtube.com形式
        if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                return params.get("v", [None])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]

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
                transcript_obj = api.fetch(video_id, languages=["en"])
                transcript = transcript_obj.to_raw_data()
                logger.info(f"Found transcript in English for video {video_id}")
            except Exception:
                # 古いAPIスタイルでフォールバック
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[lang, "en"]
                )
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
        # デフォルト: プレーンテキスト
        return "\n".join([item["text"] for item in transcript])


def format_timestamp(seconds):
    """秒数をSRTタイムスタンプ形式に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")


@app.route("/")
def index():
    """メインページ"""
    return render_template("index.html")


@app.route("/health")
def health():
    """ヘルスチェックエンドポイント（Cloud Run用）"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "youtube_api": "configured" if youtube else "not configured",
        }
    )


@app.route("/extract", methods=["POST"])
def extract():
    """字幕抽出エンドポイント"""
    try:
        data = request.json
        url = data.get("url")
        lang = data.get("lang", "ja")
        format_type = data.get("format", "txt")

        if not url:
            return jsonify({"error": "URLが指定されていません"}), 400

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
            "total_segments": len(transcript),
            "total_duration": sum(item["duration"] for item in transcript),
            "language": lang,
        }

        response_data = {
            "success": True,
            "video_id": video_id,
            "title": title,
            "transcript": formatted_transcript,
            "stats": stats,
        }

        logger.info(f"Successfully processed video {video_id}")
        return jsonify(response_data)

    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return (
            jsonify({"success": False, "error": "予期しないエラーが発生しました"}),
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


@app.errorhandler(404)
def not_found(e):
    """404エラーハンドラー"""
    return jsonify({"error": "エンドポイントが見つかりません"}), 404


@app.errorhandler(500)
def server_error(e):
    """500エラーハンドラー"""
    logger.error(f"Server error: {e}")
    return jsonify({"error": "サーバーエラーが発生しました"}), 500


if __name__ == "__main__":
    # Cloud Run環境かローカル環境かを判定
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if is_cloud_run:
        logger.info(f"Starting Cloud Run server on port {PORT}")
        app.run(host="0.0.0.0", port=PORT, debug=False)
    else:
        # ローカル開発環境
        logger.info(f"Starting local development server on port {PORT}")
        app.run(host="127.0.0.1", port=PORT, debug=True)
