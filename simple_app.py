"""
YouTube Transcript Extractor - Simple Version
シンプルで確実に動作するバージョン
"""

import json
import logging
import os
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

import google.generativeai as genai
import googleapiclient.discovery
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from youtube_transcript_api import (NoTranscriptFound, TranscriptsDisabled,
                                    YouTubeTranscriptApi)

# ロギング設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Flask アプリケーション設定
app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# 環境変数読み込み
load_dotenv()

# APIキー設定
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# YouTube API初期化
youtube = None
if YOUTUBE_API_KEY:
    try:
        youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=YOUTUBE_API_KEY
        )
        logger.info("YouTube API initialized successfully")
    except Exception as e:
        logger.error(f"YouTube API initialization failed: {e}")

# Gemini API初期化
gemini_client = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_client = genai
        logger.info("Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"Gemini API initialization failed: {e}")


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
        logger.error(f"Error extracting video ID: {e}")
        raise


def get_video_title(video_id):
    """動画タイトルを取得"""
    if not youtube:
        return f"Video ID: {video_id}"

    try:
        request = youtube.videos().list(part="snippet", id=video_id)
        response = request.execute()

        if "items" in response and len(response["items"]) > 0:
            return response["items"][0]["snippet"]["title"]
        else:
            return f"Video ID: {video_id}"
    except Exception as e:
        logger.error(f"Error getting video title: {e}")
        return f"Video ID: {video_id}"


def get_transcript(video_id, lang="ja"):
    """字幕を取得"""
    try:
        logger.info(f"Getting transcript for video {video_id}")

        # 日本語字幕を試行
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            logger.info(f"Successfully got {lang} transcript")
            return transcript
        except:
            # 英語字幕を試行
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            logger.info("Successfully got English transcript")
            return transcript

    except NoTranscriptFound:
        raise ValueError("この動画には字幕が存在しません")
    except TranscriptsDisabled:
        raise ValueError("この動画の字幕は無効化されています")
    except Exception as e:
        raise ValueError(f"字幕の取得に失敗しました: {str(e)}")


def format_transcript(transcript):
    """字幕をテキスト形式でフォーマット"""
    return " ".join([item["text"] for item in transcript])


def format_with_gemini(text):
    """Gemini AIを使用してテキストを整形"""
    if not gemini_client:
        return text

    try:
        prompt = f"""以下のYouTube字幕テキストを読みやすく整形してください。

【制約】:
- 文字を変更・追加・削除しないでください
- 内容の要約は行わないでください

【整形作業】:
1. 文の区切りで改行してください
2. 読みやすさを重視してください

テキスト:
{text}

整形結果:"""

        model = gemini_client.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini formatting error: {e}")
        return text


def summarize_with_gemini(text):
    """Gemini AIを使用してテキストを要約"""
    if not gemini_client:
        return ""

    try:
        prompt = f"""以下のYouTube動画の字幕を要約してください。

重要なポイントを箇条書きで整理してください。

字幕テキスト:
{text}

要約:"""

        model = gemini_client.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini summarization error: {e}")
        return ""


@app.route("/")
def index():
    """メインページ"""
    return render_template("index.html")


@app.route("/health")
def health():
    """ヘルスチェック"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "youtube_api": "ok" if youtube else "not configured",
            "gemini_api": "ok" if gemini_client else "not configured",
        }
    )


@app.route("/extract", methods=["POST"])
def extract():
    """字幕抽出エンドポイント"""
    try:
        data = request.json
        url = data.get("url")
        lang = data.get("lang", "ja")

        if not url:
            return jsonify({"error": "URLが必要です"}), 400

        # 動画ID取得
        video_id = get_video_id(url)
        logger.info(f"Processing video: {video_id}")

        # タイトル取得
        title = get_video_title(video_id)

        # 字幕取得
        transcript = get_transcript(video_id, lang)

        # テキストフォーマット
        text = format_transcript(transcript)

        # Gemini AIで整形・要約
        formatted_text = text
        summary = ""

        if gemini_client:
            formatted_text = format_with_gemini(text)
            summary = summarize_with_gemini(formatted_text)

        response_data = {
            "success": True,
            "video_id": video_id,
            "title": title,
            "transcript": formatted_text,
            "summary": summary,
            "stats": {"segments": len(transcript), "characters": len(text)},
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


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8765))
    logger.info(f"Starting simple YouTube transcript app on port {port}")
    app.run(host="127.0.0.1", port=port, debug=True)
