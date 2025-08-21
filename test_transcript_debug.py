#!/usr/bin/env python3
"""
字幕抽出デバッグ用テストスクリプト
確実に字幕があるテスト動画で問題を特定
"""

from youtube_transcript_api import (NoTranscriptFound, TranscriptsDisabled,
                                    YouTubeTranscriptApi)


def test_transcript_extraction():
    # 確実に字幕があるテスト動画
    test_videos = [
        ("TED Talk", "arj7oStGLkU"),  # TED: Do schools kill creativity?
        ("Google I/O", "lyRPyRKHO8M"),  # Google I/O 2023 keynote
        ("Microsoft", "8WVe3aIcNVU"),  # Microsoft Build 2023
    ]

    for name, video_id in test_videos:
        print(f"\n🧪 テスト中: {name} (ID: {video_id})")
        try:
            # 利用可能な字幕言語を確認
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            print(f"  📋 利用可能な字幕:")
            for transcript in transcripts:
                lang_code = getattr(transcript, "language_code", "unknown")
                lang_name = getattr(transcript, "language", "Unknown")
                is_generated = getattr(transcript, "is_generated", False)
                print(
                    f"    - {lang_code}: {lang_name} {'(自動生成)' if is_generated else '(手動)'}"
                )

            # 英語字幕を試行
            print(f"  🔍 英語字幕取得中...")
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
                transcript_text = " ".join(
                    [item["text"] for item in data[:3]]
                )  # 最初の3セグメントのみ
                print(f"  ✅ 成功: {transcript_text[:100]}...")
                break  # 成功したらテスト終了
            except Exception as e:
                print(f"  ❌ 英語字幕取得失敗: {e}")

            # 日本語字幕を試行
            print(f"  🔍 日本語字幕取得中...")
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=["ja"])
                transcript_text = " ".join([item["text"] for item in data[:3]])
                print(f"  ✅ 成功: {transcript_text[:100]}...")
                break
            except Exception as e:
                print(f"  ❌ 日本語字幕取得失敗: {e}")

        except Exception as e:
            print(f"  💥 動画アクセス失敗: {e}")
            continue

    print(f"\n🧪 デバッグテスト完了")


if __name__ == "__main__":
    test_transcript_extraction()
