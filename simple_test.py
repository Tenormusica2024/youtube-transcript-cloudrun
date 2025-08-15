#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube字幕取得の簡易テスト
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# UTF-8設定
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import requests
from youtube_transcript_api import YouTubeTranscriptApi


def test_simple_transcript(video_id):
    """シンプルなYouTube字幕取得テスト"""
    print(f"テスト動画ID: {video_id}")

    # Method 1: YouTube Transcript API (正しい使用方法 - fetch)
    try:
        print("Method 1: YouTube Transcript API fetch")
        api = YouTubeTranscriptApi()
        fetched_transcript = api.fetch(video_id)
        transcript = fetched_transcript.to_raw_data()
        print(f"成功: {len(transcript)}個のセグメント取得")
        text = " ".join([item["text"] for item in transcript])
        print(f"テキスト長: {len(text)}文字")
        print(f"サンプル: {text[:100]}...")
        return text
    except Exception as e:
        print(f"失敗: {e}")

    # Method 2: 言語指定あり
    try:
        print("Method 2: 言語指定 (en)")
        api = YouTubeTranscriptApi()
        fetched_transcript = api.fetch(video_id, languages=["en"])
        transcript = fetched_transcript.to_raw_data()
        print(f"成功: {len(transcript)}個のセグメント取得")
        text = " ".join([item["text"] for item in transcript])
        print(f"テキスト長: {len(text)}文字")
        print(f"サンプル: {text[:100]}...")
        return text
    except Exception as e:
        print(f"失敗: {e}")

    return None


def test_app_endpoint(transcript_text):
    """アプリのエンドポイントをテスト"""
    print("\n--- アプリエンドポイントテスト ---")

    try:
        import requests

        url = "http://localhost:5000/extract"
        data = {"transcript_text": transcript_text, "lang": "en", "format": "txt"}

        response = requests.post(url, json=data)
        print(f"レスポンスコード: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("エンドポイントテスト成功!")
                print(
                    f"整形済みテキスト長: {len(result.get('formatted_transcript', ''))}"
                )
                print(f"要約テキスト長: {len(result.get('summary', ''))}")
            else:
                print(f"エラー: {result.get('error')}")
        else:
            print(f"HTTPエラー: {response.text}")
    except Exception as e:
        print(f"エンドポイントテスト失敗: {e}")


def main():
    print("YouTube字幕取得テスト開始")

    # テスト用動画ID（Rick Astley - Never Gonna Give You Up）
    video_id = "dQw4w9WgXcQ"

    # 字幕取得テスト
    transcript_text = test_simple_transcript(video_id)

    if transcript_text:
        print("\n字幕取得成功!")

        # アプリのエンドポイントをテスト
        test_app_endpoint(transcript_text)
    else:
        print("\n字幕取得失敗")


if __name__ == "__main__":
    main()
