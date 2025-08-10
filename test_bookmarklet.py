#!/usr/bin/env python3
"""
YouTube Transcript Bookmarklet版 テストスイート
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

def test_health_check(base_url):
    """ヘルスチェックテスト"""
    print("🔍 ヘルスチェックテスト...")
    
    try:
        response = requests.get(f"{base_url}/healthz", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ヘルスチェック成功")
            print(f"   ステータス: {data.get('status')}")
            print(f"   バージョン: {data.get('version')}")
            print(f"   Gemini AI: {'有効' if data.get('features', {}).get('gemini_ai') else '無効'}")
            return True
        else:
            print(f"❌ ヘルスチェック失敗 (ステータス: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ ヘルスチェックエラー: {e}")
        return False

def test_cors_headers(base_url):
    """CORS設定テスト"""
    print("\n🌐 CORS設定テスト...")
    
    try:
        headers = {
            'Origin': 'https://www.youtube.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        }
        
        response = requests.options(f"{base_url}/api/summarize", headers=headers, timeout=10)
        
        if response.status_code == 200:
            cors_origin = response.headers.get('Access-Control-Allow-Origin')
            cors_methods = response.headers.get('Access-Control-Allow-Methods')
            
            print(f"✅ CORS設定確認完了")
            print(f"   Origin: {cors_origin}")
            print(f"   Methods: {cors_methods}")
            return True
        else:
            print(f"❌ CORSテスト失敗 (ステータス: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ CORSテストエラー: {e}")
        return False

def test_summarize_api(base_url):
    """要約APIテスト"""
    print("\n🤖 要約APIテスト...")
    
    # テスト用の字幕データ
    test_transcript = """
    こんにちは、皆さん。今日はAIについてお話しします。
    人工知能は現代社会において重要な技術となっています。
    機械学習やディープラーニングの発展により、様々な分野で活用されています。
    今後もAI技術の進歩が期待されています。
    """
    
    test_data = {
        "videoId": "test123",
        "transcript": test_transcript.strip()
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://www.youtube.com'
        }
        
        response = requests.post(
            f"{base_url}/api/summarize", 
            json=test_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print(f"✅ 要約API成功")
                print(f"   動画ID: {data.get('videoId')}")
                print(f"   要約: {data.get('summary', '')[:100]}...")
                print(f"   モード: {data.get('meta', {}).get('mode', 'unknown')}")
                return True
            else:
                print(f"❌ 要約API失敗: {data.get('error')}")
                return False
                
        else:
            print(f"❌ 要約API失敗 (ステータス: {response.status_code})")
            print(f"   レスポンス: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 要約APIエラー: {e}")
        return False

def test_rate_limiting(base_url):
    """レート制限テスト"""
    print("\n⏱️ レート制限テスト...")
    
    test_data = {
        "videoId": "rate_limit_test",
        "transcript": "短いテスト用の字幕です。"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://www.youtube.com'
    }
    
    success_count = 0
    rate_limited = False
    
    try:
        # 短時間で複数リクエストを送信
        for i in range(5):
            response = requests.post(
                f"{base_url}/api/summarize", 
                json=test_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                break
            
            time.sleep(1)  # 1秒間隔
        
        print(f"✅ レート制限テスト完了")
        print(f"   成功リクエスト: {success_count}/5")
        print(f"   レート制限発動: {'はい' if rate_limited else 'いいえ'}")
        
        return True
        
    except Exception as e:
        print(f"❌ レート制限テストエラー: {e}")
        return False

def test_static_files(base_url):
    """静的ファイル配信テスト"""
    print("\n📄 静的ファイル配信テスト...")
    
    try:
        response = requests.get(base_url, timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # ランディングページの重要な要素をチェック
            required_elements = [
                'YouTube Transcript Extractor',
                'bookmarklet',
                'ブックマークバー',
                'API設定'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print(f"✅ ランディングページ配信成功")
                print(f"   ページサイズ: {len(content)} bytes")
                return True
            else:
                print(f"⚠️ ランディングページに不足要素: {missing_elements}")
                return False
                
        else:
            print(f"❌ ランディングページ取得失敗 (ステータス: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ 静的ファイルテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("🧪 YouTube Transcript Bookmarklet テストスイート")
    print("=" * 60)
    print(f"⏰ テスト開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Base URL取得
    base_url = os.environ.get('TEST_URL')
    if not base_url:
        print("\n❌ TEST_URL環境変数が設定されていません")
        print("例: export TEST_URL=https://your-service-xxxxx.a.run.app")
        sys.exit(1)
    
    base_url = base_url.rstrip('/')
    print(f"🎯 テスト対象: {base_url}")
    
    # テスト実行
    tests = [
        ("ヘルスチェック", test_health_check),
        ("CORS設定", test_cors_headers),
        ("要約API", test_summarize_api),
        ("レート制限", test_rate_limiting),
        ("静的ファイル", test_static_files)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func(base_url)
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}でエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 テスト結果サマリー")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS ✅" if result else "FAIL ❌"
        print(f"{test_name:<20} {status}")
    
    print(f"\n🎯 総合結果: {passed}/{total} パス ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 すべてのテストが成功！")
        print("🚀 ポートフォリオでの使用準備完了")
        print(f"\n📋 次のステップ:")
        print(f"1. ブラウザで {base_url} にアクセス")
        print(f"2. API URLに {base_url} を設定")
        print(f"3. ブックマークレットをドラッグ&ドロップ")
        print(f"4. YouTubeでテスト実行")
    else:
        print("\n⚠️ 一部のテストが失敗しました")
        print("📋 失敗したテストを確認してください")
    
    print(f"\n⏰ テスト完了: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)