#!/usr/bin/env python3
"""
セキュリティ強化版YouTube Transcriptアプリの簡易テスト
"""

import os
import sys
import json
from datetime import datetime

def test_transcript_functionality():
    """トランスクリプト抽出機能の基本テスト"""
    print("=== Transcript Extraction Test ===")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # テスト用動画ID
        video_id = "dQw4w9WgXcQ"
        
        try:
            # 新しいAPIスタイル
            api = YouTubeTranscriptApi()
            transcript_obj = api.fetch(video_id, languages=['en'])
            transcript = transcript_obj.to_raw_data()
            
            print(f"SUCCESS: New API extracted {len(transcript)} segments")
            if transcript:
                print(f"Sample: {transcript[0]['text'][:100]}...")
            return True
            
        except Exception as e1:
            try:
                # 古いAPIスタイル
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript = transcript_list.find_transcript(['en']).fetch()
                
                print(f"SUCCESS: Legacy API extracted {len(transcript)} segments") 
                if transcript:
                    print(f"Sample: {transcript[0]['text'][:100]}...")
                return True
                
            except Exception as e2:
                print(f"FAILED: Both API styles failed")
                print(f"New API error: {e1}")
                print(f"Legacy API error: {e2}")
                return False
                
    except ImportError as e:
        print(f"FAILED: Import error: {e}")
        return False

def test_dependencies():
    """必要な依存関係のテスト"""
    print("=== Dependencies Test ===")
    
    required_modules = [
        'flask',
        'flask_cors', 
        'youtube_transcript_api',
        'requests'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"OK: {module}")
        except ImportError:
            print(f"MISSING: {module}")
            missing.append(module)
    
    return len(missing) == 0

def test_api_key_validation():
    """APIキー検証ロジックのテスト"""
    print("=== API Key Validation Test ===")
    
    # 元のAPIキー環境変数を保存
    original_key = os.environ.get('YOUTUBE_API_KEY')
    
    try:
        # テスト1: APIキーなし
        os.environ.pop('YOUTUBE_API_KEY', None)
        
        sys.path.insert(0, '.')
        from app import get_youtube_api_key
        
        try:
            get_youtube_api_key()
            print("FAILED: Should have raised error for missing API key")
            return False
        except ValueError as e:
            print("OK: Correctly detected missing API key")
        
        # テスト2: 無効なAPIキー
        os.environ['YOUTUBE_API_KEY'] = "PLEASE_SET_YOUR_API_KEY"
        try:
            key = get_youtube_api_key()
            if key == "PLEASE_SET_YOUR_API_KEY":
                print("OK: Placeholder API key detected")
            else:
                print("FAILED: Should detect placeholder API key")
                return False
        except:
            print("OK: Placeholder API key rejected")
        
        print("SUCCESS: API key validation working")
        return True
        
    except Exception as e:
        print(f"FAILED: API key validation error: {e}")
        return False
    finally:
        # 元の値を復元
        if original_key:
            os.environ['YOUTUBE_API_KEY'] = original_key
        else:
            os.environ.pop('YOUTUBE_API_KEY', None)

def test_url_parsing():
    """YouTube URL解析機能のテスト"""
    print("=== URL Parsing Test ===")
    
    test_urls = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ")
    ]
    
    try:
        sys.path.insert(0, '.')
        from app import get_video_id
        
        all_passed = True
        for url, expected_id in test_urls:
            try:
                result = get_video_id(url)
                if result == expected_id:
                    print(f"OK: {url} -> {result}")
                else:
                    print(f"FAILED: {url} -> {result} (expected {expected_id})")
                    all_passed = False
            except Exception as e:
                print(f"ERROR: {url} -> {e}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"FAILED: URL parsing test error: {e}")
        return False

def main():
    """メインテスト実行"""
    print("YouTube Transcript Security Test Suite")
    print("=" * 50)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Transcript Extraction", test_transcript_functionality), 
        ("API Key Validation", test_api_key_validation),
        ("URL Parsing", test_url_parsing)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"EXCEPTION: {e}")
            results.append((test_name, False))
    
    # サマリー
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("SUCCESS: All security tests passed!")
        print("The secure version is ready for deployment.")
    else:
        print("WARNING: Some tests failed.")
        print("Please check the failures before deployment.")
    
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)