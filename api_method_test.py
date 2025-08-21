#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_correct_api_methods():
    """YouTube Transcript APIの正しいメソッドをテスト"""

    print("=== YouTube API Method Test ===")

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        print("[OK] Import successful")

        # 利用可能なメソッドを確認
        methods = [
            method for method in dir(YouTubeTranscriptApi) if not method.startswith("_")
        ]
        print(f"[INFO] Available methods: {methods}")

        # テスト動画ID (Rick Astley - 確実に字幕がある動画)
        video_id = "dQw4w9WgXcQ"
        print(f"[INFO] Testing with video ID: {video_id}")

        # Method 1: fetch を試す（インスタンスメソッド）
        print("\n--- Testing fetch method (instance) ---")
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id)
            print(f"[OK] instance.fetch() worked! Got {len(transcript)} segments")

            if transcript:
                first_segment = transcript[0]
                print(f"[INFO] First segment type: {type(first_segment)}")
                print(f"[INFO] First segment: {first_segment}")

                # テキスト抽出方法をテスト
                if hasattr(first_segment, "text"):
                    print("[INFO] Using .text attribute")
                    sample_text = " ".join([seg.text for seg in transcript[:3]])
                elif isinstance(first_segment, dict) and "text" in first_segment:
                    print("[INFO] Using dict['text'] access")
                    sample_text = " ".join([seg["text"] for seg in transcript[:3]])
                else:
                    print(f"[INFO] Unknown format: {first_segment}")
                    sample_text = str(transcript[:3])

                print(f"[INFO] Sample text: {sample_text[:100]}...")

                return transcript  # 成功した場合はここで終了

        except Exception as e:
            print(f"[ERROR] fetch() failed: {e}")

        # Method 2: list を試す（インスタンスメソッド）
        print("\n--- Testing list method (instance) ---")
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            print(f"[OK] instance.list() worked! Got: {transcript_list}")
            return transcript_list
        except Exception as e:
            print(f"[ERROR] instance.list() failed: {e}")

        # Method 3: 言語指定でfetch
        print("\n--- Testing fetch with language ---")
        try:
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=["en"])
            print(f"[OK] fetch with language worked! Got {len(transcript)} segments")
            return transcript
        except Exception as e:
            print(f"[ERROR] fetch with language failed: {e}")

        print("\n[ERROR] All methods failed!")
        return None

    except Exception as e:
        print(f"[CRITICAL] Import or setup failed: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = test_correct_api_methods()
    if result:
        print(f"\n[SUCCESS] Found working method! Result type: {type(result)}")
    else:
        print("\n[FAILURE] No working method found")
