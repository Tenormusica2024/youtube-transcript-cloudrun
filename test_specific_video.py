#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_specific_video_filler_removal():
    """指定された動画でフィラー除去テスト"""

    print("=== 指定動画フィラー除去テスト ===")
    print()

    # ユーザー指定のYouTube URL
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"

    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("指定動画でフィラー除去機能をテスト中...")
        print(f"対象動画: {test_url}")
        print()

        response = requests.post(
            api_url,
            json={"url": test_url, "lang": "ja", "generate_summary": True},
            headers={"Content-Type": "application/json"},
            timeout=60,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")

                print("[SUCCESS] フィラー除去処理完了")
                print()
                print("=== 比較結果 ===")
                print(f"動画タイトル: {data.get('title', '不明')}")
                print(f"セグメント数: {data.get('stats', {}).get('segments', '不明')}")
                print(f"元テキスト文字数: {len(original):,}文字")
                print(f"整形後文字数: {len(formatted):,}文字")

                if len(original) > 0:
                    reduction = (len(original) - len(formatted)) / len(original) * 100
                    print(f"短縮率: {reduction:+.1f}%")

                print()
                print("=== 元テキスト (最初の500文字) ===")
                print(original[:500] + "..." if len(original) > 500 else original)

                print()
                print("=== 整形後テキスト (最初の500文字) ===")
                print(formatted[:500] + "..." if len(formatted) > 500 else formatted)

                print()
                print("=== 詳細フィラー除去効果確認 ===")

                # より多くのフィラー語の除去確認
                filler_patterns = {
                    "ガスも": ["ガスも"],
                    "うん": ["うん"],
                    "あ、": ["あ、"],
                    "で、": ["で、"],
                    "あれか": ["あれか"],
                    "ちゃんと": ["ちゃんと"],
                    "ですね": ["ですね"],
                    "って話": ["って話"],
                    "によって": ["によって"],
                    "とですね": ["とですね"],
                    "その他フィラー": [
                        "え〜",
                        "まあ",
                        "なんか",
                        "そう〜",
                        "ああ",
                        "ええ",
                    ],
                }

                total_removed = 0

                for category, fillers in filler_patterns.items():
                    category_removed = 0
                    for filler in fillers:
                        original_count = original.count(filler)
                        formatted_count = formatted.count(filler)
                        if original_count > formatted_count:
                            removed_count = original_count - formatted_count
                            category_removed += removed_count
                            total_removed += removed_count
                            print(
                                f"  {filler}: {original_count}回 → {formatted_count}回 ({removed_count}回除去)"
                            )

                    if category_removed == 0:
                        remaining = sum(formatted.count(f) for f in fillers)
                        if remaining > 0:
                            print(
                                f"  {category}: {remaining}回残存（除去対象パターン拡張必要）"
                            )

                print(f"\n総除去数: {total_removed}個のフィラー語/パターン")

                # 文の自然さチェック
                print()
                print("=== 文章自然性分析 ===")

                # 不自然な文頭・接続の検出
                unnatural_patterns = []
                lines = formatted.split("\n")
                for line in lines[:10]:  # 最初の10行をチェック
                    line = line.strip()
                    if line.startswith(("で、", "あ、", "うん、", "まあ、")):
                        unnatural_patterns.append(line[:20] + "...")

                if unnatural_patterns:
                    print("改善が必要な文頭パターン:")
                    for pattern in unnatural_patterns:
                        print(f"  - {pattern}")
                else:
                    print("文頭パターン: 良好")

                print()
                print("=== AI要約 (フィラー除去後テキスト使用) ===")
                summary = data.get("summary", "")
                if summary:
                    print(summary[:800] + "..." if len(summary) > 800 else summary)

                return True, original, formatted

            else:
                print(f"[ERROR] API Error: {data.get('error')}")
                return False, "", ""
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            return False, "", ""

    except Exception as e:
        print(f"[ERROR] テスト失敗: {e}")
        return False, "", ""


if __name__ == "__main__":
    success, original, formatted = test_specific_video_filler_removal()
    if success:
        print()
        print("[SUCCESS] 指定動画フィラー除去テスト完了")
        print()
        print("📋 改善提案:")
        print("1. より厳密なフィラー語パターンマッチング必要")
        print("2. 文頭の不自然なパターン（あ、で、うん等）の強化除去")
        print("3. 話し言葉特有の表現（って話、とですね等）の処理")
        print("4. 語尾の統一処理（ですね、だと思います等）")
    else:
        print()
        print("[FAILURE] テストに失敗しました")
