#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def final_verification_test():
    """最終検証テスト - 修正済みサーバーでのフィラー除去効果確認"""

    print("=== 最終検証テスト（修正済みサーバー）===")
    print()

    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("修正済みサーバーで最終検証中...")
        print(f"対象動画: {test_url}")
        print()

        response = requests.post(
            api_url,
            json={"url": test_url, "lang": "ja", "generate_summary": False},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")
                version = data.get("version", "unknown")

                print("=== 修正済みサーバー結果 ===")
                print(f"サーバーバージョン: {version}")
                print(f"元テキスト: {len(original):,} 文字")
                print(f"整形後テキスト: {len(formatted):,} 文字")

                if len(original) > 0:
                    change_rate = (len(original) - len(formatted)) / len(original) * 100
                    print(f"変化率: {change_rate:+.2f}%")

                # 重要フィラーの除去状況詳細確認
                critical_fillers = [
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
                print("=== フィラー除去詳細結果 ===")

                total_original = 0
                total_formatted = 0
                successful_removals = 0

                for filler in critical_fillers:
                    original_count = original.count(filler)
                    formatted_count = formatted.count(filler)

                    if original_count > 0:
                        total_original += original_count
                        total_formatted += formatted_count

                        removed = original_count - formatted_count
                        removal_rate = (
                            (removed / original_count) * 100
                            if original_count > 0
                            else 0
                        )

                        if removed > 0:
                            successful_removals += 1
                            status = f"SUCCESS ({removal_rate:.0f}%除去)"
                        else:
                            status = "NO CHANGE"

                        print(
                            f"  {filler}: {original_count} → {formatted_count} ({status})"
                        )

                print()

                if total_original > 0:
                    overall_removal_rate = (
                        (total_original - total_formatted) / total_original
                    ) * 100
                    print(
                        f"総合除去率: {overall_removal_rate:.1f}% ({total_original - total_formatted}/{total_original})"
                    )
                    print(
                        f"成功フィラー数: {successful_removals}/{len([f for f in critical_fillers if original.count(f) > 0])}"
                    )

                    # 成功判定
                    if overall_removal_rate >= 80 and change_rate >= 3:
                        print()
                        print("フィラー除去機能 完全成功!")
                        print(f"{overall_removal_rate:.1f}%のフィラー除去率達成")
                        print(f"{change_rate:.1f}%のテキスト短縮達成")
                        print("ユーザー要求の厳密化対応完了")
                        return True
                    elif overall_removal_rate >= 50 or change_rate >= 1:
                        print()
                        print("⚠️ フィラー除去機能 部分的成功")
                        print(
                            f"部分的改善: {overall_removal_rate:.1f}%除去, {change_rate:.1f}%短縮"
                        )
                        return False
                    else:
                        print()
                        print("フィラー除去機能 未動作")
                        print("サーバー側に問題の可能性")
                        return False
                else:
                    print("対象フィラーが見つかりませんでした")
                    return False

            else:
                print(f"API Error: {data.get('error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"Test Error: {e}")
        return False


if __name__ == "__main__":
    success = final_verification_test()

    print()
    print("=" * 70)
    if success:
        print("FINAL SUCCESS: フィラー除去機能の厳密化が完了")
        print("ユーザーの「もう少し指示の厳密化をお願いします」要求に完全対応")
        print("フィラー除去処理がより厳密に動作するよう改善されました")
    else:
        print("NEEDS INVESTIGATION: さらなる調査が必要")
        print("直接テストは成功するが、サーバー経由で問題が発生している可能性")
    print("=" * 70)
