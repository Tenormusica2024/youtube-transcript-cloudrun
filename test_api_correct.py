#!/usr/bin/env python3
"""
YouTube Transcript API動作確認テスト（正式版）
"""

from youtube_transcript_api import YouTubeTranscriptApi

def test_correct_api():
    video_id = "mmn0Il_feiY"
    
    print("=== YouTube Transcript API 正しい使い方テスト ===")
    
    try:
        # APIインスタンス作成
        api = YouTubeTranscriptApi()
        
        print(f"Video ID: {video_id}")
        
        # 1. 利用可能な字幕リストを取得
        print("\n1. 利用可能な字幕リスト取得")
        transcript_list = api.list(video_id)
        print(f"字幕リスト取得成功")
        
        # 各言語の字幕を試す
        languages_to_try = ['ja', 'en', 'auto']
        
        for lang in languages_to_try:
            try:
                print(f"\n2. {lang}字幕取得テスト")
                transcript = transcript_list.find_transcript([lang])
                data = transcript.fetch()
                
                full_text = " ".join([item["text"] for item in data])
                print(f"Success: 言語={transcript.language_code}, セグメント数={len(data)}")
                print(f"テキスト長={len(full_text)}")
                print(f"最初の50文字: {full_text[:50]}...")
                
                return {
                    "success": True,
                    "transcript": full_text,
                    "language": transcript.language_code,
                    "segments": len(data)
                }
                
            except Exception as e:
                print(f"{lang}字幕取得エラー: {e}")
                continue
                
        print("\nすべての言語で字幕取得に失敗")
        return {"success": False, "error": "No transcripts available"}
        
    except Exception as e:
        print(f"API使用エラー: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = test_correct_api()
    print(f"\n最終結果: {result}")