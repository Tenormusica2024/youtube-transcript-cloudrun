#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新しいYouTube Transcript API構造テスト
"""


def test_new_api():
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = "dQw4w9WgXcQ"  # Rick Roll
        print(f"Testing with video: {video_id}")

        # Try list method
        try:
            transcript_list = YouTubeTranscriptApi.list(video_id)
            print(f"list() success: {type(transcript_list)}")
            print(f"Content: {transcript_list}")
        except Exception as e:
            print(f"list() failed: {e}")

        # Try fetch method
        try:
            transcript_data = YouTubeTranscriptApi.fetch(video_id)
            print(f"fetch() success: {type(transcript_data)}")
            print(f"Content: {transcript_data}")
        except Exception as e:
            print(f"fetch() failed: {e}")

        # Test the class itself
        try:
            api_instance = YouTubeTranscriptApi()
            print(f"Instance created: {api_instance}")
            instance_methods = [m for m in dir(api_instance) if not m.startswith("_")]
            print(f"Instance methods: {instance_methods}")
        except Exception as e:
            print(f"Instance creation failed: {e}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_new_api()
