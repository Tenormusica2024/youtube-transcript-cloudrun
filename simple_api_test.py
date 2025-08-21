#!/usr/bin/env python3
"""
シンプルなYouTube Transcript APIテスト
"""
from youtube_transcript_api import YouTubeTranscriptApi


def simple_test():
    print("=== シンプルAPIテスト ===")

    # 確実に字幕があるYouTube動画ID
    video_ids = [
        "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up (英語字幕確実)
        "9bZkp7q19f0",  # PSY - Gangnam Style (多言語字幕)
        "kJQP7kiw5Fk",  # Luis Fonsi - Despacito (スペイン語/英語字幕)
    ]

    for video_id in video_ids:
        print(f"\n--- テスト動画: {video_id} ---")

        # 基本のget_transcript呼び出し
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            print(f"✅ 成功: {len(transcript)}件の字幕エントリ")
            if transcript:
                sample = transcript[0]
                print(f"サンプル: {sample}")
                break  # 1つ成功したら終了
        except Exception as e:
            print(f"❌ エラー: {e}")

            # 言語指定でリトライ
            for lang in ["en", "ja", "es"]:
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=[lang]
                    )
                    print(f"✅ {lang}指定成功: {len(transcript)}件")
                    if transcript:
                        sample = transcript[0]
                        print(f"サンプル: {sample}")
                        return  # 成功したら完全終了
                except Exception as e2:
                    print(f"❌ {lang}指定エラー: {e2}")


if __name__ == "__main__":
    simple_test()
