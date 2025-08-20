#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インスタンス方式のYouTube Transcript APIテスト
"""

def test_instance_api():
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Create instance
        api = YouTubeTranscriptApi()
        video_id = "dQw4w9WgXcQ"  # Rick Roll
        
        print(f"Testing instance API with video: {video_id}")
        
        # Try list method
        try:
            transcript_list = api.list(video_id)
            print(f"list() success: {type(transcript_list)}")
            print(f"List content: {transcript_list}")
            
            # If list returns transcript objects, try to fetch from them
            if hasattr(transcript_list, '__iter__'):
                for transcript in transcript_list:
                    print(f"Transcript object: {transcript}")
                    if hasattr(transcript, 'fetch'):
                        try:
                            data = transcript.fetch()
                            print(f"Fetched data: {len(data)} entries")
                            if data:
                                print(f"Sample: {data[0]}")
                            break
                        except Exception as fe:
                            print(f"Fetch from transcript failed: {fe}")
            
        except Exception as e:
            print(f"list() failed: {e}")
        
        # Try direct fetch method
        try:
            transcript_data = api.fetch(video_id)
            print(f"Direct fetch() success: {type(transcript_data)}")
            print(f"Data: {transcript_data}")
        except Exception as e:
            print(f"Direct fetch() failed: {e}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_instance_api()