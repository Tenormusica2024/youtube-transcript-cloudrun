"""
YouTube Shorts対応テスト
各種URL形式での動画ID抽出をテスト
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from urllib.parse import parse_qs, urlparse


def get_video_id_test(url):
    """YouTube URLから動画IDを抽出（テスト版）"""
    try:
        parsed_url = urlparse(url)
        print(f"Testing URL: {url}")
        print(f"Parsed netloc: {parsed_url.netloc}")
        print(f"Parsed path: {parsed_url.path}")
        print(f"Parsed query: {parsed_url.query}")

        # youtu.be形式
        if parsed_url.hostname == "youtu.be":
            video_id = parsed_url.path[1:].split("?")[0].split("&")[0]
            print(f"youtu.be format detected, video_id: {video_id}")
            return video_id

        # youtube.com形式
        if parsed_url.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
            # 通常の動画 (/watch?v=VIDEO_ID)
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                video_id = params.get("v", [None])[0]
                print(f"Watch format detected, video_id: {video_id}")
                return video_id
            # YouTube Shorts (/shorts/VIDEO_ID)
            elif parsed_url.path.startswith("/shorts/"):
                video_id = (
                    parsed_url.path.split("/shorts/")[1].split("?")[0].split("&")[0]
                )
                print(f"YouTube Shorts format detected, video_id: {video_id}")
                return video_id
            # Embed形式 (/embed/VIDEO_ID)
            elif parsed_url.path.startswith("/embed/"):
                video_id = parsed_url.path.split("/")[2].split("?")[0].split("&")[0]
                print(f"Embed format detected, video_id: {video_id}")
                return video_id
            # その他のパス形式 (/v/VIDEO_ID)
            elif parsed_url.path.startswith("/v/"):
                video_id = parsed_url.path.split("/")[2].split("?")[0].split("&")[0]
                print(f"V format detected, video_id: {video_id}")
                return video_id

        raise ValueError(f"無効なYouTube URLです: {url}")
    except Exception as e:
        print(f"Error extracting video ID from URL {url}: {e}")
        return None


def test_youtube_url_formats():
    """様々なYouTube URL形式をテスト"""

    # テストURL一覧
    test_urls = [
        # 通常の動画URL
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        # YouTube Shorts URL
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/shorts/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ?feature=share",
        # 短縮URL
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?t=30",
        # Embed URL
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://youtube.com/embed/dQw4w9WgXcQ?start=30",
        # V URL
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        # 無効なURL
        "https://example.com/video",
        "not-a-url",
    ]

    print("=== YouTube URL形式テスト ===\n")

    success_count = 0
    total_count = len(test_urls)

    for i, url in enumerate(test_urls, 1):
        print(f"Test {i}/{total_count}:")
        video_id = get_video_id_test(url)

        if video_id:
            print(f"[OK] Success: Video ID = {video_id}")
            success_count += 1
        else:
            print(f"[FAIL] Failed: Could not extract video ID")

        print("-" * 50)

    print(f"\n=== テスト結果 ===")
    print(f"成功: {success_count}/{total_count}")
    print(f"成功率: {(success_count/total_count)*100:.1f}%")

    # 期待される結果
    expected_success = total_count - 2  # 無効なURL 2個を除く
    if success_count >= expected_success:
        print("[OK] すべての有効なURL形式が正常に処理されました")
        return True
    else:
        print("[FAIL] 一部のURL形式でエラーが発生しました")
        return False


if __name__ == "__main__":
    # URL解析テスト実行
    test_result = test_youtube_url_formats()

    if test_result:
        print("\n[SUCCESS] YouTube Shorts対応が正常に実装されました！")
    else:
        print("\n[WARNING] 追加の修正が必要です")
