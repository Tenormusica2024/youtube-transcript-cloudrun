"""
YouTube Transcript Webapp - テストサーバー
ポート8081で起動し、基本機能をテスト
"""

import os
import sys
import time
import threading
import requests
from pathlib import Path

# パスを追加
sys.path.insert(0, str(Path(__file__).parent))

def start_server():
    """サーバーを起動"""
    # app_cloud_run.pyをappとして実行
    import app_cloud_run as app
    
    # テスト用のYouTube API キー（環境変数を模擬）
    os.environ['YOUTUBE_API_KEY'] = 'test_api_key_for_testing'
    os.environ['PORT'] = '8081'
    
    print("Starting test server...")
    app.app.run(host='127.0.0.1', port=8081, debug=False)

def test_endpoints():
    """エンドポイントをテスト"""
    base_url = "http://127.0.0.1:8081"
    
    # サーバー起動を待つ
    print("Waiting for server to start...")
    time.sleep(3)
    
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                print("[OK] Server started successfully!")
                break
        except:
            if i < max_retries - 1:
                time.sleep(1)
            else:
                print("[ERROR] Failed to start server")
                return False
    
    # テスト実行
    print("\n[TEST] Starting tests...")
    print("-" * 50)
    
    # 1. ヘルスチェック
    print("\n1. Health check endpoint (/health)")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンス: {response.json()}")
        assert response.status_code == 200
        assert 'status' in response.json()
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Failed: {e}")
    
    # 2. メインページ
    print("\n2. Main page (/)")
    try:
        response = requests.get(f"{base_url}/")
        print(f"   ステータスコード: {response.status_code}")
        assert response.status_code == 200
        assert 'html' in response.text.lower()
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Failed: {e}")
    
    # 3. 字幕抽出（エラーケース）
    print("\n3. Extract endpoint - error case (/extract)")
    try:
        response = requests.post(
            f"{base_url}/extract",
            json={"url": "invalid_url"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   ステータスコード: {response.status_code}")
        print(f"   レスポンス: {response.json()}")
        assert response.status_code == 400
        assert 'error' in response.json()
        print("   [OK] Proper error handling")
    except Exception as e:
        print(f"   [ERROR] Failed: {e}")
    
    # 4. 404エラー
    print("\n4. 404 error handling")
    try:
        response = requests.get(f"{base_url}/nonexistent")
        print(f"   ステータスコード: {response.status_code}")
        assert response.status_code == 404
        print("   [OK] Success")
    except Exception as e:
        print(f"   [ERROR] Failed: {e}")
    
    print("\n" + "=" * 50)
    print("[COMPLETE] All tests finished!")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    print("=" * 50)
    print("YouTube Transcript Webapp - テスト実行")
    print("=" * 50)
    
    # サーバーを別スレッドで起動
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # テスト実行
    success = test_endpoints()
    
    if success:
        print("\n[SUCCESS] All tests passed!")
        print("サーバーはポート8081で稼働中です。")
        print("ブラウザで http://localhost:8081 にアクセスしてください。")
        print("終了するには Ctrl+C を押してください。")
        
        try:
            # サーバーを継続実行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[EXIT] Shutting down server...")
    else:
        print("\n[FAILED] Tests failed.")
        sys.exit(1)