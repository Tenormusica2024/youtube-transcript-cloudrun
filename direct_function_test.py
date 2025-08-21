#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def direct_function_test():
    """直接関数テスト - サーバーを経由せずにフィラー除去をテスト"""

    print("=== 直接関数テスト（サーバー経由なし）===")

    # 1. まず実際のテキストを取得
    try:
        response = requests.post(
            "http://127.0.0.1:8087/api/extract",
            json={"url": "9Dgt8dcuH6I", "lang": "ja", "generate_summary": False},
            timeout=20,
        )

        if response.status_code != 200:
            print("API取得失敗")
            return False

        data = response.json()
        original_text = data.get("original_transcript", "")

        if not original_text:
            print("テキスト取得失敗")
            return False

        print(f"取得したテキスト長: {len(original_text)}")
        print()

    except Exception as e:
        print(f"テキスト取得エラー: {e}")
        return False

    # 2. 直接フィラー除去関数を実装・実行
    def test_format_transcript_text(original_text):
        """テスト用フィラー除去関数"""
        import re

        if not original_text or not original_text.strip():
            return original_text

        text = original_text
        print(f"直接テスト: フィラー除去開始 {len(text)}文字")

        # 実際のテキスト分析に基づく最適化パターン
        specific_fillers = [
            ("ガスも", r"ガスも\s*"),
            ("うん。", r"うん\。\s*"),
            ("うん", r"うん(?=[\s。、！？]|$)"),  # 修正: 後続が空白・句読点・文末
            ("あ、", r"あ、\s*"),
            ("で、", r"で、\s*"),
            ("あれか、", r"あれか、\s*"),
            ("あれか", r"あれか(?=[\s。、！？]|$)"),  # 修正: 後続が空白・句読点・文末
            (
                "ちゃんと",
                r"ちゃんと(?=[\s。、！？]|$)",
            ),  # 修正: 後続が空白・句読点・文末
            ("ですね", r"ですね\s*"),
            ("って話", r"って話\s*"),
            (
                "によって",
                r"によって(?=[\s。、！？]|$)",
            ),  # 修正: 後続が空白・句読点・文末
            ("とですね", r"とですね\s*"),
        ]

        removed_count = 0
        for filler_name, pattern in specific_fillers:
            old_text = text
            text = re.sub(pattern, " ", text)
            if old_text != text:
                removed = old_text.count(filler_name) - text.count(filler_name)
                removed_count += removed
                print(f"直接テスト: {filler_name} 除去 {removed}個")

        # 基本的なフィラー語も除去
        basic_fillers = [
            r"え[ー〜～]*\s*",
            r"ま[ー〜～]*\s*",
            r"あの[ー〜～]*\s*",
            r"なんか\s*",
            r"そう[ー〜～]*\s*",
            r"まあ\s*",
        ]

        for pattern in basic_fillers:
            text = re.sub(pattern, " ", text)

        # 文章整理
        text = re.sub(r"\s{2,}", " ", text)
        text = re.sub(r"([。！？])\s*([あ-んア-ン一-龯])", r"\1\n\2", text)
        text = text.strip()

        print(f"直接テスト: フィラー除去完了 {len(text)}文字 ({removed_count}個除去)")
        reduction = (
            ((len(original_text) - len(text)) / len(original_text) * 100)
            if len(original_text) > 0
            else 0
        )
        print(f"直接テスト: 短縮率 {reduction:+.1f}%")

        return text

    # 3. 直接テスト実行
    try:
        formatted_text = test_format_transcript_text(original_text)

        print()
        print("=== 直接テスト結果 ===")
        print(f"元テキスト: {len(original_text)} 文字")
        print(f"整形後: {len(formatted_text)} 文字")

        if len(original_text) > 0:
            change_rate = (
                (len(original_text) - len(formatted_text)) / len(original_text) * 100
            )
            print(f"変化率: {change_rate:+.2f}%")

        # フィラー除去効果確認
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

        total_removed = 0
        for filler in target_fillers:
            original_count = original_text.count(filler)
            formatted_count = formatted_text.count(filler)
            if original_count > 0:
                removed = original_count - formatted_count
                total_removed += removed
                print(f"{filler}: {original_count} → {formatted_count} (-{removed})")

        print(f"\n総除去数: {total_removed}")

        if total_removed > 10:
            print("\n直接テスト: フィラー除去成功")
            return True
        else:
            print("\n直接テスト: フィラー除去不十分")
            return False

    except Exception as e:
        print(f"直接テストエラー: {e}")
        return False


if __name__ == "__main__":
    success = direct_function_test()

    if success:
        print("\n=== 結論 ===")
        print("直接関数テストは成功 → サーバー側の問題の可能性")
    else:
        print("\n=== 結論 ===")
        print("直接関数テストも失敗 → パターン自体に問題")
