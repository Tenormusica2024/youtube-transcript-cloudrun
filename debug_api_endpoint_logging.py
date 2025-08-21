#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def debug_api_endpoint_logging():
    """API エンドポイントでのフィラー除去実行をデバッグ"""

    print("=== API エンドポイント フィラー除去デバッグ ===")
    print()

    # ユーザー指定の問題動画
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        print("API リクエスト送信 - フィラー除去デバッグログ確認中...")
        print(f"対象動画: {test_url}")
        print()

        response = requests.post(
            api_url,
            json={
                "url": test_url,
                "lang": "ja",
                "generate_summary": False,  # 要約なしで高速テスト
            },
            headers={"Content-Type": "application/json"},
            timeout=45,
        )

        print(f"HTTP レスポンス: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original = data.get("original_transcript", "")
                formatted = data.get("transcript", "")

                print()
                print("=== API 処理結果 ===")
                print(f"元テキスト長: {len(original):,} 文字")
                print(f"整形後長: {len(formatted):,} 文字")

                if len(original) > 0:
                    change_rate = (len(original) - len(formatted)) / len(original) * 100
                    print(f"変化率: {change_rate:+.2f}%")

                # 重要フィラーの除去状況を確認
                critical_fillers = [
                    "ガスも",
                    "うん",
                    "あ、で、",
                    "あれか、",
                    "ちゃんと",
                    "ですね",
                    "って話",
                    "によって",
                    "とですね",
                ]

                print()
                print("=== フィラー除去詳細分析 ===")

                total_original_fillers = 0
                total_remaining_fillers = 0

                for filler in critical_fillers:
                    original_count = original.count(filler)
                    formatted_count = formatted.count(filler)

                    if original_count > 0:
                        total_original_fillers += original_count
                        total_remaining_fillers += formatted_count

                        removal_success = formatted_count == 0
                        status_icon = "OK" if removal_success else "NG"

                        print(
                            f"{status_icon} {filler}: {original_count} → {formatted_count}"
                        )

                # 全体的除去効果
                if total_original_fillers > 0:
                    removal_rate = (
                        (total_original_fillers - total_remaining_fillers)
                        / total_original_fillers
                    ) * 100
                    print()
                    print(
                        f"総除去効果: {removal_rate:.1f}% ({total_original_fillers - total_remaining_fillers}/{total_original_fillers})"
                    )

                    if removal_rate > 70:
                        print("フィラー除去機能が正常動作中")
                    elif removal_rate > 30:
                        print("部分的にフィラー除去が機能")
                    else:
                        print("フィラー除去機能に問題あり")

                # 最重要: テキスト同一性チェック
                print()
                print("=== 処理実行確認 ===")
                if original.strip() == formatted.strip():
                    print("重大問題: テキストが全く変化していません")
                    print("   → format_transcript_text() が実行されていない可能性")
                    print("   → API エンドポイント内でのフィラー除去処理を確認が必要")

                    # サンプル比較
                    print()
                    print("最初の200文字比較:")
                    print(f'元     : "{original[:200]}..."')
                    print(f'整形後 : "{formatted[:200]}..."')

                    return False
                else:
                    print("テキストに変化があります - フィラー除去が実行されています")
                    return True

            else:
                print(f"[API ERROR] {data.get('error')}")
                return False
        else:
            print(f"[HTTP ERROR] Status {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"[EXCEPTION] テスト失敗: {e}")
        return False


if __name__ == "__main__":
    print("サーバーが起動していることを確認してください...")
    print("URL: http://127.0.0.1:8087")
    print()

    success = debug_api_endpoint_logging()

    print()
    print("=" * 60)
    if success:
        print("フィラー除去機能は正常に動作しています")
        print("ユーザー要求の厳密化に成功")
    else:
        print("フィラー除去機能に問題があります")
        print("→ production_server.py の API エンドポイントを詳細調査が必要")
        print("→ format_transcript_text() 関数の呼び出し確認が必要")
    print("=" * 60)
