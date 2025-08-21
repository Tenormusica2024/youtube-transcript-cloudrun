#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_filler_function_directly():
    """production_server.pyのformat_transcript_text関数を直接テスト"""
    print("=== フィラー除去関数直接テスト ===")
    print()

    # production_serverからインポート
    sys.path.append(".")
    from production_server import format_transcript_text

    # ユーザー指摘の具体的な問題文
    test_text = """ガスも 出してくれてるんですが スライドパターンの Googleスライドがないと 厳しいって話ですよね。うん。あ、で、メイン実行関数もあれか、 ちゃんと ジェミに与えておいて理解してもらうこと によって制度があるとですね。うん。"""

    print("元テキスト:")
    print(f'"{test_text}"')
    print()

    # フィラー除去実行
    try:
        result = format_transcript_text(test_text)

        print("フィラー除去後:")
        print(f'"{result}"')
        print()

        # 変化率の計算
        original_len = len(test_text)
        result_len = len(result)
        reduction = (
            ((original_len - result_len) / original_len) * 100
            if original_len > 0
            else 0
        )

        print(f"文字数変化: {original_len} → {result_len} ({reduction:.1f}%削減)")

        # 具体的フィラーの残存確認
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
        remaining = []
        removed = []

        for filler in target_fillers:
            original_count = test_text.count(filler)
            result_count = result.count(filler)
            if original_count > 0:
                if result_count == 0:
                    removed.append(f"{filler}({original_count}→0)")
                elif result_count < original_count:
                    removed.append(f"{filler}({original_count}→{result_count})")
                else:
                    remaining.append(f"{filler}({result_count})")

        print()
        if removed:
            print(f"除去成功: {', '.join(removed)}")
        if remaining:
            print(f"残存フィラー: {', '.join(remaining)}")

        # 成功判定
        success_rate = (
            len(removed)
            / len([f for f in target_fillers if test_text.count(f) > 0])
            * 100
            if target_fillers
            else 0
        )
        print(f"フィラー除去成功率: {success_rate:.1f}%")

        if success_rate >= 80:
            print("\n[SUCCESS] フィラー除去機能が正常に動作しています")
            return True
        else:
            print("\n[FAILURE] フィラー除去が不十分です")
            return False

    except Exception as e:
        print(f"[ERROR] テスト実行エラー: {e}")
        return False


if __name__ == "__main__":
    success = test_filler_function_directly()
    if success:
        print()
        print("✅ フィラー除去機能の改善が完了しました")
        print("ユーザー指摘の厳密化要求に対応済みです")
    else:
        print()
        print("❌ さらなる調整が必要です")
