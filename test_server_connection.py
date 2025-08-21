#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_server_connection():
    """サーバー接続とログ確認"""

    print("=== サーバー接続確認 ===")

    # 1. まずサーバーが生きているか確認
    try:
        response = requests.get("http://127.0.0.1:8087/")
        print(f"サーバー生存確認: {response.status_code}")
    except Exception as e:
        print(f"サーバー接続失敗: {e}")
        return False

    # 2. API endpoint が存在するか確認
    try:
        response = requests.post(
            "http://127.0.0.1:8087/api/extract",
            json={"url": "test", "lang": "ja"},
            timeout=5,
        )
        print(f"API エンドポイント確認: {response.status_code}")
        if response.status_code != 200:
            print(f"レスポンス: {response.text[:200]}")
    except Exception as e:
        print(f"API エンドポイント接続失敗: {e}")
        return False

    print("サーバー接続 OK - ログ出力の問題の可能性")
    return True


if __name__ == "__main__":
    test_server_connection()
