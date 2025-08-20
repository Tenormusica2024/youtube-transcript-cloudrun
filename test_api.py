#!/usr/bin/env python3
"""
YouTube Transcript API動作確認テスト
"""

from youtube_transcript_api import YouTubeTranscriptApi

def test_api():
    video_id = "mmn0Il_feiY"  # テスト用動画ID
    
    print("=== YouTubeTranscriptApi 動作テスト ===")
    
    try:
        print(f"Video ID: {video_id}")
        
        # 1. 日本語字幕を取得
        print("\n1. 日本語字幕取得テスト")
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja'])
        print(f"Success: 取得したセグメント数 = {len(data)}")
        print(f"最初の3セグメント: {data[:3]}")
        
        # 2. 英語字幕を取得
        print("\n2. 英語字幕取得テスト")
        data_en = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print(f"Success: 取得したセグメント数 = {len(data_en)}")
        
    except Exception as e:
        print(f"個別取得エラー: {e}")
        
        # 3. 利用可能な字幕リストを取得
        try:
            print("\n3. 利用可能な字幕リスト取得テスト")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            print(f"利用可能な字幕:")
            for transcript in transcript_list:
                print(f"  - 言語: {transcript.language_code}, 生成済み: {transcript.is_generated}")
                
                # 最初の字幕を試してみる
                data = transcript.fetch()
                print(f"    取得成功: {len(data)} セグメント")
                break
                
        except Exception as list_e:
            print(f"リスト取得エラー: {list_e}")

if __name__ == "__main__":
    test_api()