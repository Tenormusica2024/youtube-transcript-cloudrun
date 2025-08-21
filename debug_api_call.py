#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def debug_api_call():
    """API呼び出しをデバッグして実際のフィラー除去処理を確認"""

    print("=== API呼び出しデバッグ ===")
    print()

    # 簡単なテスト用URL
    test_url = "https://www.youtube.com/watch?v=BQLRduuiGR4"  # 前回成功したURL

    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("APIリクエスト送信...")
        print(f"URL: {test_url}")
        print()

        response = requests.post(
            api_url,
            json={
                "url": test_url,
                "lang": "ja",
                "generate_summary": False,  # 要約無しで高速テスト
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        print(f"レスポンス状況: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")

                print(f"[OK] API成功")
                print(f"元テキスト長: {len(original)}文字")
                print(f"整形後長: {len(formatted)}文字")

                if len(original) > 0:
                    change = (len(original) - len(formatted)) / len(original) * 100
                    print(f"変化率: {change:+.2f}%")

                # 最初の部分を比較
                print()
                print("=== テキスト比較 (最初の200文字) ===")
                print("元:")
                print(f'"{original[:200]}..."')
                print()
                print("整形後:")
                print(f'"{formatted[:200]}..."')

                # 同じかどうかチェック
                if original.strip() == formatted.strip():
                    print()
                    print("❌ 問題: テキストがまったく変化していません")
                    print("format_transcript_text()関数が正しく動作していない可能性")
                else:
                    print()
                    print("✅ テキストに変化があります")

                return True

            else:
                print(f"[ERROR] API Error: {data.get('error')}")
                return False
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"[ERROR] テスト失敗: {e}")
        return False


if __name__ == "__main__":
    debug_api_call()
