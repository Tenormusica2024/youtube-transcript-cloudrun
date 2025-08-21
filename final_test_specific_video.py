#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def final_test_specific_video():
    """最終テスト: 指定動画でのフィラー除去確認"""

    print("=== 最終フィラー除去テスト ===")
    print()

    # ユーザー指定のYouTube URL
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"

    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("改善されたフィラー除去機能で最終テスト実行中...")
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
                print("=== 改善結果 ===")
                print(f"動画タイトル: {data.get('title', '不明')}")
                print(f"セグメント数: {data.get('stats', {}).get('segments', '不明')}")
                print(f"元テキスト文字数: {len(original):,}文字")
                print(f"整形後文字数: {len(formatted):,}文字")

                if len(original) > 0:
                    reduction = (len(original) - len(formatted)) / len(original) * 100
                    print(f"短縮率: {reduction:+.1f}%")

                # 重要: 実際のフィラー除去効果を確認
                target_fillers = [
                    "ガスも",
                    "うん",
                    "あ、",
                    "で、",
                    "あれか",
                    "ちゃんと",
                    "ですね",
                    "って話",
                    "によって",
                    "とですね",
                ]

                print()
                print("=== フィラー除去効果詳細 ===")

                total_removed = 0
                for filler in target_fillers:
                    original_count = original.count(filler)
                    formatted_count = formatted.count(filler)
                    if original_count > 0:
                        removed_count = original_count - formatted_count
                        total_removed += removed_count
                        removal_rate = (removed_count / original_count) * 100
                        status = (
                            "✓完全除去"
                            if formatted_count == 0
                            else f"部分除去({removal_rate:.0f}%)"
                        )
                        print(
                            f"  {filler}: {original_count}回 → {formatted_count}回 ({status})"
                        )

                # 成功判定
                overall_success = total_removed > 30  # 30個以上のフィラー除去で成功
                improvement_rate = (
                    total_removed / sum(original.count(f) for f in target_fillers)
                ) * 100

                print(
                    f"\\n総除去効果: {total_removed}個のフィラー除去 ({improvement_rate:.1f}%改善)"
                )

                print()
                print("=== 整形後テキスト抜粋 (最初の300文字) ===")
                print(formatted[:300] + "..." if len(formatted) > 300 else formatted)

                if overall_success and reduction > 10:
                    print()
                    print("🎉 [SUCCESS] ユーザー指摘のフィラー除去要求に完全対応")
                    print(f"✅ {improvement_rate:.1f}%のフィラー語を除去")
                    print(f"✅ {reduction:.1f}%のテキスト短縮を実現")
                    print("✅ より厳密な指示処理が完了しました")
                    return True
                else:
                    print()
                    print("⚠️  [PARTIAL] 改善は見られますが、さらなる調整が必要")
                    return False

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
    success = final_test_specific_video()
    if success:
        print()
        print("=" * 50)
        print("フィラー除去機能の厳密化が完了しました")
        print("ユーザーの要求に応じて処理精度を向上させました")
        print("=" * 50)
    else:
        print()
        print("=" * 50)
        print("追加の調整が必要な可能性があります")
        print("=" * 50)
