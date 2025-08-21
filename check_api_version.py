#!/usr/bin/env python3
"""
YouTube Transcript APIバージョンと機能確認
"""
import youtube_transcript_api
from youtube_transcript_api import YouTubeTranscriptApi

print(f"YouTube Transcript API バージョン: {youtube_transcript_api.__version__}")
print("利用可能なメソッド:")
methods = [method for method in dir(YouTubeTranscriptApi) if not method.startswith("_")]
for method in methods:
    print(f"  - {method}")

# 実際のget_transcriptメソッドの使い方をテスト
print("\n=== get_transcript テスト ===")
try:
    # 有名なTED Talkで英語字幕があることが確実なもの
    video_id = "jNQXAC9IVRw"
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print(f"成功: {len(transcript)}件の字幕を取得")
    if transcript:
        print(f"最初の字幕: {transcript[0]}")
except Exception as e:
    print(f"get_transcript エラー: {e}")

    # 言語指定でのテスト
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        print(f"英語指定成功: {len(transcript)}件の字幕を取得")
        if transcript:
            print(f"最初の字幕: {transcript[0]}")
    except Exception as e2:
        print(f"英語指定もエラー: {e2}")
