"""
YouTube Transcript Cloud Run App Test - Transcript Only
字幕抽出機能のみをテスト（YouTube Data API不要）
"""

import os
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を設定（APIキー無しでも字幕抽出をテスト）
os.environ["YOUTUBE_API_KEY"] = "not-needed-for-transcript-test"
os.environ["PORT"] = "8081"


def test_transcript_extraction_only():
    """字幕抽出のみテスト（APIキー不要）"""
    print("\n[TEST] Testing transcript extraction without YouTube Data API...")

    try:
        from app_cloud_run import get_transcript, get_video_id

        # テスト用動画（Rick Roll - 確実に字幕がある）
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        # 1. URL解析テスト
        print(f"\n[TEST 1] URL parsing: {test_url}")
        video_id = get_video_id(test_url)
        print(f"[OK] Video ID extracted: {video_id}")

        # 2. 字幕抽出テスト
        print(f"\n[TEST 2] Transcript extraction for video: {video_id}")
        transcript = get_transcript(video_id, lang="en")  # 英語字幕を取得
        print(f"[OK] Transcript extracted: {len(transcript)} segments")

        # 3. データ構造確認
        if transcript and len(transcript) > 0:
            first_segment = transcript[0]
            required_keys = ["text", "start", "duration"]
            for key in required_keys:
                if key not in first_segment:
                    raise ValueError(f"Missing key: {key}")
            print(f"[OK] Transcript data structure is valid")

            # サンプル出力
            sample_text = " ".join([item["text"] for item in transcript[:3]])
            print(f"[INFO] Sample text: {sample_text}")

            # 統計
            total_duration = sum(item["duration"] for item in transcript)
            print(f"[INFO] Total segments: {len(transcript)}")
            print(f"[INFO] Total duration: {total_duration:.1f} seconds")

            return True
        else:
            raise ValueError("Empty transcript received")

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False


def test_different_formats():
    """異なる出力フォーマットのテスト"""
    print("\n[TEST] Testing different output formats...")

    try:
        from app_cloud_run import format_transcript, get_transcript

        video_id = "dQw4w9WgXcQ"
        transcript = get_transcript(video_id, lang="en")

        # TXTフォーマット
        txt_output = format_transcript(transcript, "txt")
        print(f"[OK] TXT format: {len(txt_output)} characters")

        # JSONフォーマット
        json_output = format_transcript(transcript, "json")
        print(f"[OK] JSON format: {len(json_output)} characters")

        # SRTフォーマット
        srt_output = format_transcript(transcript, "srt")
        print(f"[OK] SRT format: {len(srt_output)} characters")

        return True

    except Exception as e:
        print(f"[ERROR] Format test failed: {e}")
        return False


def test_url_variations():
    """様々なURL形式のテスト"""
    print("\n[TEST] Testing various URL formats...")

    try:
        from app_cloud_run import get_video_id

        test_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/v/dQw4w9WgXcQ",
        ]

        expected_id = "dQw4w9WgXcQ"

        for url in test_urls:
            video_id = get_video_id(url)
            if video_id != expected_id:
                raise ValueError(f"URL parsing failed: {url} -> {video_id}")
            print(f"[OK] {url} -> {video_id}")

        return True

    except Exception as e:
        print(f"[ERROR] URL test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Cloud Run App Test")
    print("Testing core functionality without YouTube Data API")
    print("=" * 60)

    success = True

    # URL解析テスト
    if not test_url_variations():
        success = False
        print("[FAILED] URL variation test failed")
    else:
        print("[PASSED] URL variation test passed")

    # 字幕抽出テスト
    if not test_transcript_extraction_only():
        success = False
        print("[FAILED] Transcript extraction test failed")
    else:
        print("[PASSED] Transcript extraction test passed")

    # フォーマットテスト
    if not test_different_formats():
        success = False
        print("[FAILED] Format test failed")
    else:
        print("[PASSED] Format test passed")

    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] All core functionality tests passed!")
        print("The Cloud Run app is ready for deployment.")
        print("\nNext steps:")
        print("1. Get YouTube Data API key from Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print("2. Replace 'your-api-key-here' in .env file with actual API key")
        print("3. Deploy to Cloud Run or run locally")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] Some tests failed.")
        print("Please check the implementation and try again.")
        print("=" * 60)

    sys.exit(0 if success else 1)
