#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import traceback

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_youtube_api():
    """YouTube Transcript APIのデバッグテスト"""

    print("=== YouTube Transcript API Debug Test ===")
    print()

    # 1. ライブラリのインポートテスト
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        print("[OK] YouTubeTranscriptApi import successful")
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return

    # 2. テスト用の動画ID (公開されている有名な動画)
    test_videos = [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "9bZkp7q19f0",  # PSY - GANGNAM STYLE
        "kJQP7kiw5Fk",  # Despacito
    ]

    for video_id in test_videos:
        print(f"\n--- Testing Video ID: {video_id} ---")

        # 3. 利用可能なメソッドの確認
        try:
            # 利用可能なメソッドを確認
            api_methods = [
                method
                for method in dir(YouTubeTranscriptApi)
                if not method.startswith("_")
            ]
            print(f"[INFO] Available API methods: {api_methods}")

        except Exception as e:
            print(f"[ERROR] Failed to get API methods: {e}")
            continue

        # 4. 字幕取得テスト (複数言語)
        test_languages = ["ja", "en", "auto"]

        for lang in test_languages:
            try:
                print(f"\n  Testing language: {lang}")

                # 新しいAPIメソッドを使用
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[lang]
                )

                if transcript and len(transcript) > 0:
                    print(f"    [OK] Success! Got {len(transcript)} segments")

                    # 最初の3セグメントを表示
                    for i, segment in enumerate(transcript[:3]):
                        text = segment.get("text", "No text")
                        start = segment.get("start", 0)
                        print(f"    [{start:.1f}s] {text[:50]}...")
                        if i >= 2:
                            break

                    # 成功したら次の動画へ
                    print(
                        f"    Total characters: {sum(len(s.get('text', '')) for s in transcript)}"
                    )
                    break

                else:
                    print(f"    [WARN] Empty transcript for {lang}")

            except Exception as e:
                print(f"    [ERROR] Failed for {lang}: {str(e)[:100]}...")

        # 成功した動画があれば詳細テストを実行
        if transcript:
            break

    # 5. 詳細なエラー処理テスト
    print(f"\n--- Error Handling Test ---")
    invalid_video_ids = ["invalid123", "abcdefghijk"]

    for invalid_id in invalid_video_ids:
        try:
            YouTubeTranscriptApi.get_transcript(invalid_id)
        except Exception as e:
            print(
                f"[OK] Correctly handled invalid ID '{invalid_id}': {type(e).__name__}"
            )

    print(f"\n=== Test Complete ===")


if __name__ == "__main__":
    try:
        test_youtube_api()
    except Exception as e:
        print(f"Critical error: {e}")
        traceback.print_exc()
