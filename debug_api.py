#!/usr/bin/env python3
"""
YouTube Transcript APIの詳細デバッグ
"""
from youtube_transcript_api import YouTubeTranscriptApi


def debug_video_transcript(video_id):
    print(f"=== デバッグ: {video_id} ===")

    try:
        # 利用可能な字幕言語を確認
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        print(f"利用可能な字幕:")

        for transcript in transcript_list:
            print(f"  言語: {transcript.language}, コード: {transcript.language_code}")

        # 任意の字幕を取得
        try:
            transcript = transcript_list.find_transcript(["ja"])
            data = transcript.fetch()
            print(f"日本語字幕取得成功: {len(data)}件")
            print(f"サンプル: {data[0] if data else 'データなし'}")
        except:
            try:
                transcript = transcript_list.find_transcript(["en"])
                data = transcript.fetch()
                print(f"英語字幕取得成功: {len(data)}件")
                print(f"サンプル: {data[0] if data else 'データなし'}")
            except Exception as e:
                print(f"字幕取得失敗: {e}")

    except Exception as e:
        print(f"エラー: {e}")


if __name__ == "__main__":
    # テスト用動画ID
    test_videos = [
        "jNQXAC9IVRw",  # TED Talk
        "dQw4w9WgXcQ",  # Rick Roll (字幕確実)
        "9bZkp7q19f0",  # PSY - Gangnam Style
    ]

    for video_id in test_videos:
        debug_video_transcript(video_id)
        print("-" * 50)
