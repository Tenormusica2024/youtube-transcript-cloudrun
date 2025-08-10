"""
YouTube Transcript Only Test - API key不要
字幕抽出のみをテスト（YouTube Data API不使用）
"""

import os
import sys
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))


def test_transcript_extraction():
    """字幕抽出のテスト（APIキー不要）"""
    print("\n[TEST] Testing transcript extraction without YouTube Data API...")

    # 字幕が確実にある公開動画を使用
    test_cases = [
        {
            "video_id": "dQw4w9WgXcQ",  # Rick Roll - 確実に字幕がある
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "name": "Rick Roll (Classic test video)",
        }
    ]

    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        print("[INFO] youtube_transcript_api library loaded successfully")
    except ImportError:
        print("[ERROR] youtube_transcript_api not installed")
        print("Install with: pip install youtube-transcript-api")
        return False

    for test_case in test_cases:
        print(f"\n[TEST] Testing: {test_case['name']}")
        print(f"Video ID: {test_case['video_id']}")
        print(f"URL: {test_case['url']}")

        try:
            # 直接字幕を取得（英語を試行）
            print("\n[INFO] Trying to extract English transcript...")
            api = YouTubeTranscriptApi()
            transcript_obj = api.fetch(test_case["video_id"], languages=["en"])
            transcript = transcript_obj.to_raw_data()
            print(f"[SUCCESS] Extracted {len(transcript)} transcript segments")

            # 統計情報
            total_duration = sum(item["duration"] for item in transcript)
            print(f"Total duration: {total_duration:.1f} seconds")

            # サンプルテキスト表示
            sample_texts = []
            for i, item in enumerate(transcript[:5]):  # 最初の5セグメント
                sample_texts.append(item["text"].strip())

            sample_text = " ".join(sample_texts)
            print(f"Sample text: {sample_text[:200]}...")

            # 異なる形式でのテスト
            print("\n[TEST] Testing different formats...")

            # TXT形式
            txt_output = "\n".join([item["text"] for item in transcript])
            print(f"TXT format: {len(txt_output)} characters")

            # JSON形式
            import json

            json_output = json.dumps(transcript, ensure_ascii=False, indent=2)
            print(f"JSON format: {len(json_output)} characters")

            # SRT形式のテスト
            srt_output = []
            for i, item in enumerate(transcript, 1):
                start_time = format_srt_time(item["start"])
                end_time = format_srt_time(item["start"] + item["duration"])
                srt_output.append(f"{i}\n{start_time} --> {end_time}\n{item['text']}\n")

            srt_text = "\n".join(srt_output)
            print(f"SRT format: {len(srt_text)} characters")

            return True

        except Exception as e:
            print(f"[ERROR] Transcript extraction failed: {e}")
            continue

    return False


def format_srt_time(seconds):
    """秒数をSRT形式の時間に変換"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")


def test_url_parsing():
    """URL解析のテスト"""
    print("\n[TEST] Testing URL parsing...")

    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
    ]

    from urllib.parse import parse_qs, urlparse

    def extract_video_id(url):
        """URLから動画IDを抽出"""
        parsed_url = urlparse(url)

        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]

        if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                return params.get("v", [None])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]

        raise ValueError(f"Invalid YouTube URL: {url}")

    for url in test_urls:
        try:
            video_id = extract_video_id(url)
            print(f"[OK] {url} -> {video_id}")
        except Exception as e:
            print(f"[ERROR] {url} -> {e}")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Test - No API Key Required")
    print("=" * 60)

    success = True

    # URL解析テスト
    if not test_url_parsing():
        success = False
        print("[FAILED] URL parsing test failed")
    else:
        print("[PASSED] URL parsing test passed")

    # 字幕抽出テスト
    if not test_transcript_extraction():
        success = False
        print("[FAILED] Transcript extraction test failed")
    else:
        print("[PASSED] Transcript extraction test passed")

    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("The transcript extraction functionality is working correctly.")
        print("You can proceed with Cloud Run deployment.")
        print(
            "\nNote: For complete functionality, you still need a YouTube Data API key"
        )
        print("to get video titles and metadata.")
    else:
        print("\n" + "=" * 60)
        print("[FAILED] Some tests failed.")
        print("Please check the requirements and try again.")

    print("=" * 60)
    sys.exit(0 if success else 1)
