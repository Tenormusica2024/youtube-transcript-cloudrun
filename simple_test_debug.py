#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def simple_test_debug():
    """シンプルなテストでサーバーログを確認"""

    print("=== シンプルデバッグテスト ===")

    # より短いテスト用URL
    test_url = "BQLRduuiGR4"  # 短いID形式でテスト
    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("最小限のリクエストでデバッグログ確認...")
        print(f"動画ID: {test_url}")

        response = requests.post(
            api_url,
            json={
                "url": test_url,
                "lang": "ja",
                "generate_summary": False,  # 要約なしで高速
            },
            headers={"Content-Type": "application/json"},
            timeout=20,
        )

        print(f"レスポンス: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")

                print()
                print(f"成功: 元={len(original)} → 整形={len(formatted)}")

                # サーバーログを確認するための待機時間
                print("サーバーログを確認してください...")

                return True
            else:
                print(f"API失敗: {data.get('error')}")
                return False
        else:
            print(f"HTTP失敗: {response.status_code}")
            return False

    except Exception as e:
        print(f"エラー: {e}")
        return False


if __name__ == "__main__":
    simple_test_debug()
