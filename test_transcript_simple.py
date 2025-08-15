#!/usr/bin/env python3
"""
YouTube字幕取得の簡易テストスクリプト
"""

import re
import sys

import requests
from youtube_transcript_api import YouTubeTranscriptApi


def test_youtube_transcript_api(video_id):
    """YouTube Transcript APIのテスト"""
    print(f"=== YouTube Transcript API テスト (動画ID: {video_id}) ===")

    try:
        # 利用可能な言語を確認
        transcript_list = YouTubeTranscriptApi().list_transcripts(video_id)
        print("利用可能な字幕:")
        for transcript in transcript_list:
            print(
                f"  - {transcript.language} ({transcript.language_code}) [自動生成: {transcript.is_generated}]"
            )

        # 日本語字幕を取得試行
        try:
            transcript = YouTubeTranscriptApi().get_transcript(
                video_id, languages=["ja"]
            )
            print(f"\n✅ 日本語字幕取得成功: {len(transcript)}個のセグメント")
            print("最初の3セグメント:")
            for i, segment in enumerate(transcript[:3]):
                print(f"  {i+1}. {segment['text']} (開始: {segment['start']:.2f}s)")
            return True
        except Exception as ja_error:
            print(f"❌ 日本語字幕取得失敗: {ja_error}")

        # 英語字幕を取得試行
        try:
            transcript = YouTubeTranscriptApi().get_transcript(
                video_id, languages=["en"]
            )
            print(f"\n✅ 英語字幕取得成功: {len(transcript)}個のセグメント")
            print("最初の3セグメント:")
            for i, segment in enumerate(transcript[:3]):
                print(f"  {i+1}. {segment['text']} (開始: {segment['start']:.2f}s)")
            return True
        except Exception as en_error:
            print(f"❌ 英語字幕取得失敗: {en_error}")

        # 自動生成字幕を取得試行
        try:
            transcript = YouTubeTranscriptApi().get_transcript(video_id)
            print(f"\n✅ 自動字幕取得成功: {len(transcript)}個のセグメント")
            print("最初の3セグメント:")
            for i, segment in enumerate(transcript[:3]):
                print(f"  {i+1}. {segment['text']} (開始: {segment['start']:.2f}s)")
            return True
        except Exception as auto_error:
            print(f"❌ 自動字幕取得失敗: {auto_error}")

    except Exception as e:
        print(f"❌ YouTube Transcript API全体エラー: {e}")

    return False


def test_timedtext_api(video_id):
    """Timedtext APIのテスト"""
    print(f"\n=== Timedtext API テスト (動画ID: {video_id}) ===")

    languages = ["ja", "en"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    for lang in languages:
        try:
            url = f"https://www.youtube.com/api/timedtext?lang={lang}&v={video_id}"
            print(f"試行URL: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            print(f"レスポンス: {response.status_code}, 長さ: {len(response.text)}")

            if response.status_code == 200 and response.text.strip():
                # XMLをパース
                texts = re.findall(r"<text[^>]*>([^<]+)</text>", response.text)
                if texts:
                    print(f"✅ {lang}字幕取得成功: {len(texts)}個のテキストセグメント")
                    print("最初の3セグメント:")
                    for i, text in enumerate(texts[:3]):
                        print(f"  {i+1}. {text}")
                    return True
                else:
                    print(f"❌ {lang}字幕: XMLにテキストが見つかりません")
            else:
                print(f"❌ {lang}字幕: レスポンスが無効")

        except Exception as e:
            print(f"❌ {lang}字幕取得エラー: {e}")

    return False


def extract_video_id(url):
    """YouTube URLから動画IDを抽出"""
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "youtube.com" in url:
        if "v=" in url:
            return url.split("v=")[1].split("&")[0]
    return url  # 既に動画IDの場合


def main():
    print("YouTube字幕取得テストスクリプト")

    # テスト用の動画URL/ID
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (first YouTube video)
    ]

    if len(sys.argv) > 1:
        test_urls = [sys.argv[1]]

    for url in test_urls:
        video_id = extract_video_id(url)
        print(f"\n{'='*60}")
        print(f"テスト動画: {url}")
        print(f"動画ID: {video_id}")
        print(f"{'='*60}")

        # 両方のAPIをテスト
        api_success = test_youtube_transcript_api(video_id)
        timedtext_success = test_timedtext_api(video_id)

        print(f"\n結果:")
        print(f"  YouTube Transcript API: {'OK' if api_success else 'NG'}")
        print(f"  Timedtext API: {'OK' if timedtext_success else 'NG'}")

        if not api_success and not timedtext_success:
            print("この動画は字幕が取得できません")

        print("\n" + "-" * 60)


if __name__ == "__main__":
    main()
