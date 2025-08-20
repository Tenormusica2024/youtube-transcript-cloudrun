#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Transcript API完全テスト
"""

def test_api():
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        print("Import OK")
        
        # Available methods
        methods = [m for m in dir(YouTubeTranscriptApi) if not m.startswith('_')]
        print(f"Available methods: {methods}")
        
        # Test with a video that definitely has captions
        video_id = "dQw4w9WgXcQ"  # Rick Roll - has English captions
        print(f"Testing video: {video_id}")
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            print(f"SUCCESS: Got {len(transcript)} transcript entries")
            if transcript:
                print(f"First entry: {transcript[0]}")
                return True
        except Exception as e:
            print(f"get_transcript failed: {e}")
            return False
            
    except ImportError as e:
        print(f"Import failed: {e}")
        return False
    except Exception as e:
        print(f"General error: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    print(f"Test result: {'PASS' if success else 'FAIL'}")