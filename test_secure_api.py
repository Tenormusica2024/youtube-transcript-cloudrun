#!/usr/bin/env python3
"""
セキュリティ強化版YouTube Transcriptアプリのテストスクリプト
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

def test_api_key_setup():
    """APIキーが正しく設定されているかテスト"""
    print("🔍 APIキー設定のテスト...")
    
    # 環境変数からAPIキーを取得
    api_key = os.environ.get('YOUTUBE_API_KEY')
    
    if not api_key:
        print("❌ 環境変数 YOUTUBE_API_KEY が設定されていません")
        print("💡 以下のコマンドでAPIキーを設定してください:")
        print("   set YOUTUBE_API_KEY=your_api_key_here")
        return False
    
    if api_key == "PLEASE_SET_YOUR_API_KEY":
        print("❌ APIキーがデフォルト値のままです")
        print("💡 実際のYouTube Data API v3キーを設定してください")
        return False
    
    if len(api_key) < 30:
        print("❌ APIキーが短すぎます（無効な可能性）")
        return False
        
    print(f"✅ APIキーが設定されています (長さ: {len(api_key)})")
    return True

def test_youtube_api_direct():
    """YouTube Data API v3に直接アクセスしてテスト"""
    print("\n🔍 YouTube Data API v3の直接テスト...")
    
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ APIキーが設定されていません")
        return False
    
    # テスト用の動画ID (Rick Astley - Never Gonna Give You Up)
    video_id = "dQw4w9WgXcQ"
    
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet',
            'id': video_id,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                title = data['items'][0]['snippet']['title']
                print(f"✅ API接続成功！タイトル取得: {title}")
                return True
            else:
                print("❌ 動画が見つかりませんでした")
                return False
        elif response.status_code == 403:
            print("❌ API認証エラー：APIキーが無効です")
            print(f"レスポンス: {response.text}")
            return False
        else:
            print(f"❌ APIエラー (ステータス: {response.status_code})")
            print(f"レスポンス: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API接続エラー: {e}")
        return False

def test_transcript_extraction():
    """youtube-transcript-apiを使用したトランスクリプト抽出テスト"""
    print("\n🔍 トランスクリプト抽出のテスト...")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        
        # テスト用動画ID (字幕がある英語動画)
        video_id = "dQw4w9WgXcQ"
        
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            
            if transcript and len(transcript) > 0:
                print(f"✅ トランスクリプト取得成功！セグメント数: {len(transcript)}")
                print(f"📝 最初のセグメント: {transcript[0]['text'][:50]}...")
                return True
            else:
                print("❌ トランスクリプトが空です")
                return False
                
        except TranscriptsDisabled:
            print("❌ この動画はトランスクリプトが無効化されています")
            return False
        except NoTranscriptFound:
            print("❌ 指定された言語のトランスクリプトが見つかりません")
            return False
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False

def test_local_app():
    """ローカルでアプリを起動してテスト"""
    print("\n🔍 ローカルアプリケーションのテスト...")
    
    # アプリがすでに動いているかチェック
    try:
        response = requests.get('http://127.0.0.1:8080/health', timeout=5)
        if response.status_code == 200:
            print("✅ アプリケーションが既に動作中です")
            return test_app_endpoints()
    except:
        pass
    
    print("🚀 アプリケーションを起動します...")
    print("💡 別のターミナルで以下のコマンドを実行してください:")
    print("   cd C:\\Users\\Tenormusica\\youtube_secure_updated")
    print("   python app.py")
    print("\n⏳ アプリの起動を15秒待ちます...")
    
    for i in range(15, 0, -1):
        print(f"⏰ {i}秒...")
        time.sleep(1)
    
    return test_app_endpoints()

def test_app_endpoints():
    """アプリケーションのエンドポイントをテスト"""
    print("\n🔍 アプリケーションエンドポイントのテスト...")
    
    base_url = "http://127.0.0.1:8080"
    
    # ヘルスチェックテスト
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ ヘルスチェック成功: {health_data}")
        else:
            print(f"❌ ヘルスチェック失敗 (ステータス: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False
    
    # トランスクリプト抽出テスト
    try:
        test_data = {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "lang": "en",
            "format": "txt"
        }
        
        response = requests.post(f"{base_url}/extract", 
                               json=test_data, 
                               timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ トランスクリプト抽出API成功!")
                print(f"📝 タイトル: {result.get('title', 'Unknown')}")
                print(f"📊 統計: {result.get('stats', {})}")
                return True
            else:
                print(f"❌ トランスクリプト抽出失敗: {result.get('error')}")
                return False
        else:
            print(f"❌ API呼び出し失敗 (ステータス: {response.status_code})")
            print(f"レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ トランスクリプト抽出エラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🔒 YouTube Transcript セキュリティ強化版 テストスイート")
    print("=" * 60)
    print(f"⏰ テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 1. APIキー設定テスト
    test_results.append(("APIキー設定", test_api_key_setup()))
    
    # 2. YouTube API直接テスト
    test_results.append(("YouTube Data API v3", test_youtube_api_direct()))
    
    # 3. トランスクリプト抽出テスト
    test_results.append(("トランスクリプト抽出", test_transcript_extraction()))
    
    # 4. ローカルアプリテスト
    test_results.append(("ローカルアプリケーション", test_local_app()))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 テスト結果: {passed}/{total} パス ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 すべてのテストが成功しました！")
        print("💡 セキュリティ強化版アプリが正常に機能しています")
    else:
        print("⚠️  一部のテストが失敗しました")
        print("💡 失敗したテストの詳細を確認してください")
    
    print(f"\n⏰ テスト完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()