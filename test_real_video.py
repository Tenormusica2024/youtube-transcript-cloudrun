#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_real_video_filler_removal():
    """実際のYouTube動画でフィラー除去テスト"""

    print("=== 実動画フィラー除去テスト ===")
    print()

    # テスト用YouTube URL (話し言葉が多い動画)
    test_url = "https://www.youtube.com/watch?v=BQLRduuiGR4"  # 前回のテストで11,339文字の長編動画

    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("実動画でフィラー除去機能をテスト中...")
        print(f"対象動画: {test_url}")
        print()

        response = requests.post(
            api_url,
            json={"url": test_url, "lang": "ja", "generate_summary": True},
            headers={"Content-Type": "application/json"},
            timeout=45,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")

                print("[SUCCESS] フィラー除去処理完了")
                print()
                print("=== 比較結果 ===")
                print(f"元テキスト文字数: {len(original):,}文字")
                print(f"整形後文字数: {len(formatted):,}文字")

                if len(original) > 0:
                    reduction = (len(original) - len(formatted)) / len(original) * 100
                    print(f"短縮率: {reduction:+.1f}%")

                print()
                print("=== 元テキスト (最初の300文字) ===")
                print(original[:300] + "..." if len(original) > 300 else original)

                print()
                print("=== 整形後テキスト (最初の300文字) ===")
                print(formatted[:300] + "..." if len(formatted) > 300 else formatted)

                print()
                print("=== フィラー除去効果確認 ===")

                # フィラー語の除去確認
                common_fillers = ["え〜", "まあ", "うん", "あの〜", "なんか", "そう〜"]
                removed_fillers = []

                for filler in common_fillers:
                    original_count = original.count(filler)
                    formatted_count = formatted.count(filler)
                    if original_count > formatted_count:
                        removed_fillers.append(
                            f"{filler}: {original_count}→{formatted_count}"
                        )

                if removed_fillers:
                    print("除去されたフィラー:")
                    for removal in removed_fillers:
                        print(f"  {removal}")
                else:
                    print("フィラー語: この動画には該当するフィラー語が少ない")

                print()
                print("=== AI要約 (フィラー除去後) ===")
                summary = data.get("summary", "")
                if summary:
                    print(summary[:500] + "..." if len(summary) > 500 else summary)

                return True

            else:
                print(f"[ERROR] API Error: {data.get('error')}")
                return False
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] テスト失敗: {e}")
        return False


if __name__ == "__main__":
    success = test_real_video_filler_removal()
    if success:
        print()
        print("[SUCCESS] 実動画フィラー除去テスト完了")
        print("整形済みタブでフィラー除去されたテキストが確認できます")
    else:
        print()
        print("[FAILURE] テストに失敗しました")
