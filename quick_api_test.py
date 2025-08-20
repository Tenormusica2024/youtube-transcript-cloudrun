#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time

def test_fixed_api():
    """修正されたAPIの動作テスト"""
    
    print("=== YouTube API修正後テスト ===")
    print()
    
    # テスト用YouTube URL (Rick Astley - 字幕確実にある)
    test_data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "lang": "en",
        "generate_summary": True
    }
    
    api_url = "http://127.0.0.1:8087/api/extract"
    
    print(f"Testing URL: {test_data['url']}")
    print(f"API Endpoint: {api_url}")
    print()
    
    try:
        print("Sending POST request...")
        start_time = time.time()
        
        response = requests.post(
            api_url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        end_time = time.time()
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f}s")
        print()
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("[OK] SUCCESS! API修正成功")
                print(f"Title: {data.get('title', 'N/A')}")
                print(f"Segments: {data.get('stats', {}).get('segments', 'N/A')}")
                print(f"Characters: {data.get('stats', {}).get('characters', 'N/A')}")
                print(f"Language: {data.get('stats', {}).get('language', 'N/A')}")
                print(f"Version: {data.get('version', 'N/A')}")
                print()
                
                # 字幕テキストの一部を表示
                transcript = data.get('transcript', '')
                if transcript:
                    print("[TEXT] Formatted Transcript (first 200 chars):")
                    print(transcript[:200] + "..." if len(transcript) > 200 else transcript)
                    print()
                
                # AI要約の一部を表示
                summary = data.get('summary', '')
                if summary and 'AI要約' in summary:
                    print("[AI] AI Summary (first 300 chars):")
                    print(summary[:300] + "..." if len(summary) > 300 else summary)
                    print()
                
                return True
                
            else:
                print("[ERROR] API Error:")
                print(f"Error: {data.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"[ERROR] HTTP Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection Error: サーバーが起動していません")
        print("サーバーを起動してください: python production_server.py")
        return False
        
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout Error: リクエストがタイムアウトしました")
        return False
        
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = test_fixed_api()
    if success:
        print("[SUCCESS] 修正完了！YouTube Transcript Appが正常に動作しています")
    else:
        print("[WARN] まだ問題があります。詳細なデバッグが必要です")