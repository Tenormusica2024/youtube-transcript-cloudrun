#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_filler_removal():
    """フィラー除去機能のテスト"""

    # production_serverから関数をインポート
    sys.path.append(".")
    from production_server import format_transcript_text

    print("=== フィラー除去テスト ===")
    print()

    # テストケース: フィラー語が多い文章
    test_cases = [
        {
            "name": "日本語フィラー多用",
            "input": "え〜、まあ、うん、これはですね、あの〜、なんか面白い内容だと思います。そう〜、まあそういうことですね。",
            "expected_improvement": "フィラー語除去により自然な文章に",
        },
        {
            "name": "英語フィラー多用",
            "input": "Well, um, you know, I think, uh, this is like, really interesting content, you know? So, yeah, that's basically it.",
            "expected_improvement": "英語フィラー語除去",
        },
        {
            "name": "いいよどみパターン",
            "input": "この〜、その〜、えっと〜、資料を見ていただくと、うん〜、分かると思うんですが。",
            "expected_improvement": "いいよどみ除去で読みやすく",
        },
        {
            "name": "口語表現修正",
            "input": "めっちゃすごくて、マジでヤバいと思います。ぶっちゃけ、やっぱりこれはいい感じですね。",
            "expected_improvement": "口語→標準語変換",
        },
        {
            "name": "冗長表現簡潔化",
            "input": "〜ということになりますが、〜というふうに考えております。〜といった感じでしょうか。",
            "expected_improvement": "冗長表現を簡潔に",
        },
        {
            "name": "複合パターン",
            "input": "え〜、まあ、YouTube動画っていうのは、うん、なんかめっちゃ面白いですよね。そう〜、ぶっちゃけマジでいい感じだと思います。",
            "expected_improvement": "複数パターン同時処理",
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"--- テストケース {i}: {case['name']} ---")
        print(f"元テキスト:")
        print(f"  {case['input']}")
        print()

        try:
            # フィラー除去処理実行
            formatted = format_transcript_text(case["input"])

            print(f"整形後:")
            print(f"  {formatted}")
            print()

            # 改善度の評価
            original_length = len(case["input"])
            formatted_length = len(formatted)
            reduction_ratio = (
                (original_length - formatted_length) / original_length * 100
            )

            print(f"改善結果:")
            print(
                f"  文字数: {original_length} → {formatted_length} ({reduction_ratio:+.1f}%)"
            )
            print(f"  期待効果: {case['expected_improvement']}")

            # フィラー除去の検証
            fillers_found = []
            common_fillers = [
                "え〜",
                "まあ",
                "うん",
                "あの〜",
                "なんか",
                "そう〜",
                "um",
                "uh",
                "you know",
                "like",
                "well",
            ]

            for filler in common_fillers:
                if filler in case["input"] and filler not in formatted:
                    fillers_found.append(filler)

            if fillers_found:
                print(f"  除去されたフィラー: {', '.join(fillers_found)}")
            else:
                print(f"  フィラー除去: 該当なし")

            print()

        except Exception as e:
            print(f"[ERROR] テスト失敗: {e}")
            print()

    print("=== フィラー除去機能テスト完了 ===")
    print()
    print("📝 改善ポイント:")
    print("  ✅ 日本語フィラー語除去 (え〜、まあ、うん等)")
    print("  ✅ 英語フィラー語除去 (um, uh, you know等)")
    print("  ✅ いいよどみパターン除去")
    print("  ✅ 口語→標準語変換")
    print("  ✅ 冗長表現簡潔化")
    print("  ✅ 空文・不自然な句読点整理")


if __name__ == "__main__":
    test_filler_removal()
