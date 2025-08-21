#!/usr/bin/env python3
import sys
import time

import requests


def test_server():
    url = "http://127.0.0.1:8085"

    print("🔍 サーバー接続テスト開始...")
    print(f"URL: {url}")

    for attempt in range(5):
        try:
            print(f"試行 {attempt + 1}/5...")
            response = requests.get(f"{url}/health", timeout=5)

            if response.status_code == 200:
                print("✅ サーバー起動成功！")
                print(f"ステータス: {response.status_code}")
                print(f"レスポンス: {response.text[:200]}...")
                print(f"📱 ブラウザで {url} にアクセスしてください")
                return True
            else:
                print(f"⚠️  ステータス {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"❌ 接続失敗 (試行 {attempt + 1})")
            if attempt < 4:
                print("3秒待機中...")
                time.sleep(3)
        except Exception as e:
            print(f"❌ エラー: {e}")
            break

    print("❌ サーバー起動失敗")
    return False


if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)
