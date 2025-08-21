#!/usr/bin/env python3
"""
YouTube Transcript API動作確認テスト（修正版）
"""

try:
    from youtube_transcript_api import YouTubeTranscriptApi

    print("Import successful")
    print(f"Available methods: {dir(YouTubeTranscriptApi)}")

    # 正しいインスタンスメソッド呼び出し
    api = YouTubeTranscriptApi()
    print(
        f"Instance methods: {[method for method in dir(api) if not method.startswith('_')]}"
    )

except Exception as e:
    print(f"Import error: {e}")

# 別の方法でテスト
try:
    import youtube_transcript_api

    print(f"\nModule contents: {dir(youtube_transcript_api)}")

    # モジュールレベルの関数があるかチェック
    if hasattr(youtube_transcript_api, "get_transcript"):
        print("Found get_transcript at module level")

except Exception as e:
    print(f"Module inspection error: {e}")
