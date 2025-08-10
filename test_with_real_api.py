"""
YouTube Transcript Webapp - Real API Test
実際のAPIキーでのテストスクリプト
"""

import json
import os
import sys
import threading
import time
from pathlib import Path

import requests

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))


def get_api_key():
    """APIキーを取得（複数の方法を試行）"""
    # 1. 環境変数から
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if api_key:
        print(f"[INFO] Found API key in environment variable")
        return api_key

    # 2. .envファイルから
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("YOUTUBE_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        if (
                            api_key
                            and not api_key.startswith("your-")
                            and not api_key.startswith("AIzaSyBF-")
                        ):
                            print(f"[INFO] Found API key in .env file")
                            return api_key
        except Exception as e:
            print(f"[ERROR] Reading .env file: {e}")

    # 3. 手動入力
    print("\n[SETUP] YouTube API key not found.")
    print("Please get your API key from: https://console.cloud.google.com/")
    print("1. Create a project")
    print("2. Enable YouTube Data API v3")
    print("3. Create credentials (API Key)")

    api_key = input("\nEnter your YouTube API key: ").strip()
    if api_key:
        # .envファイルに保存
        try:
            with open(".env", "w") as f:
                f.write(f"YOUTUBE_API_KEY={api_key}\n")
                f.write("PORT=8081\n")
            print("[INFO] API key saved to .env file")
        except Exception as e:
            print(f"[WARNING] Could not save to .env: {e}")
        return api_key

    return None


def test_youtube_api(api_key):
    """YouTube API の基本テスト"""
    print("\n[TEST] Testing YouTube Data API...")

    # Rick Roll動画でテスト（公開動画で確実に存在）
    test_video_id = "dQw4w9WgXcQ"
    test_url = f"https://www.googleapis.com/youtube/v3/videos"

    params = {"part": "snippet", "id": test_video_id, "key": api_key}

    try:
        response = requests.get(test_url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) > 0:
                title = data["items"][0]["snippet"]["title"]
                print(f"[OK] API is working! Test video title: '{title}'")
                return True
            else:
                print("[ERROR] No video data returned")
                return False
        else:
            print(f"[ERROR] API request failed: {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] API test failed: {e}")
        return False


def test_transcript_extraction():
    """実際の字幕抽出テスト"""
    print("\n[TEST] Testing transcript extraction...")

    # 字幕が確実にある動画を使用
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll
        "https://youtu.be/dQw4w9WgXcQ",  # Short URL format
    ]

    for test_url in test_urls:
        print(f"\n[TEST] Testing URL: {test_url}")
        try:
            # 字幕抽出ライブラリを直接テスト
            from youtube_transcript_api import YouTubeTranscriptApi

            video_id = (
                test_url.split("v=")[-1].split("&")[0]
                if "v=" in test_url
                else test_url.split("/")[-1]
            )
            print(f"Video ID: {video_id}")

            # 利用可能な字幕を確認
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print("Available transcripts:")

            available_languages = []
            for transcript in transcript_list:
                print(
                    f"  - {transcript.language_code}: {transcript.language} (Generated: {transcript.is_generated})"
                )
                available_languages.append(transcript.language_code)

            # 英語の字幕を取得（Rick Rollには英語字幕がある）
            if "en" in available_languages:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en"]
                )
                print(f"[OK] Transcript extracted! {len(transcript)} segments")

                # 最初の数行を表示
                sample_text = []
                for i, item in enumerate(transcript[:3]):
                    sample_text.append(item["text"])

                print(f"Sample text: {' '.join(sample_text)}")
                return True
            else:
                print("[WARNING] No English transcript available for test video")
                return False

        except Exception as e:
            print(f"[ERROR] Transcript extraction failed: {e}")

    return False


def start_server_and_test():
    """サーバー起動と統合テスト"""
    print("\n[TEST] Starting integrated server test...")

    # APIキー設定
    api_key = get_api_key()
    if not api_key:
        print("[ERROR] No API key available")
        return False

    # YouTube API テスト
    if not test_youtube_api(api_key):
        print("[ERROR] YouTube API test failed")
        return False

    # 字幕抽出テスト
    if not test_transcript_extraction():
        print("[WARNING] Transcript extraction test failed, but continuing...")

    # Cloud Run互換サーバー起動
    os.environ["YOUTUBE_API_KEY"] = api_key
    os.environ["PORT"] = "8081"

    try:
        import app_cloud_run as app

        def run_server():
            print("[INFO] Starting server on port 8081...")
            app.app.run(host="127.0.0.1", port=8081, debug=False)

        # サーバーを別スレッドで起動
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # サーバー起動を待つ
        time.sleep(3)

        # 統合テスト実行
        base_url = "http://127.0.0.1:8081"

        # ヘルスチェック
        print("\n[TEST] Health check...")
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        # 実際の字幕抽出テスト
        print("\n[TEST] Real transcript extraction...")
        test_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "lang": "en",
            "format": "txt",
        }

        response = requests.post(
            f"{base_url}/extract",
            json=test_data,
            timeout=30,  # 字幕取得には時間がかかる場合がある
        )

        print(f"Status: {response.status_code}")
        result = response.json()

        if result.get("success"):
            print(f"[SUCCESS] Title: {result.get('title', 'Unknown')}")
            print(f"Video ID: {result.get('video_id', 'Unknown')}")
            stats = result.get("stats", {})
            print(f"Segments: {stats.get('total_segments', 'Unknown')}")
            print(f"Duration: {stats.get('total_duration', 'Unknown')} seconds")

            transcript = result.get("transcript", "")
            if transcript:
                print(f"Transcript preview: {transcript[:200]}...")
                print("\n[SUCCESS] All tests passed!")

                # ブラウザでテストするか確認
                print(f"\nServer is running at: {base_url}")
                print("You can test in browser or press Ctrl+C to stop")

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n[INFO] Server stopped")

                return True
            else:
                print("[ERROR] No transcript content received")
        else:
            print(f"[ERROR] Extraction failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"[ERROR] Server test failed: {e}")

    return False


if __name__ == "__main__":
    print("=" * 60)
    print("YouTube Transcript Webapp - Real API Test")
    print("=" * 60)

    success = start_server_and_test()

    if success:
        print("\n[COMPLETE] All tests successful! Ready for Cloud Run deployment.")
    else:
        print("\n[FAILED] Some tests failed. Please check the setup.")
        print("\nNext steps:")
        print("1. Get YouTube Data API key from Google Cloud Console")
        print("2. Set YOUTUBE_API_KEY environment variable")
        print("3. Run this test again")

    sys.exit(0 if success else 1)
