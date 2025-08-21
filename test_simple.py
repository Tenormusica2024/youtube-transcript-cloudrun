#!/usr/bin/env python3
"""
簡単なテスト用スクリプト - YouTubeの短い動画でテスト
"""

import os
import sys

# 現在のディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_transcript_tool import (extract_video_id, format_transcript_text,
                                    get_transcript_local)


def test_basic_functionality():
    """基本機能のテスト"""
    print("基本機能テスト開始...")

    # テスト用の短いYouTube動画 (ニュース系の動画)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"

    print(f"テストURL: {test_url}")

    # 動画ID抽出テスト
    video_id = extract_video_id(test_url)
    print(f"抽出された動画ID: {video_id}")

    if not video_id:
        print("動画ID抽出に失敗")
        return False

    # 字幕取得テスト
    print("字幕取得中...")
    transcript, detected_lang = get_transcript_local(video_id, "auto")

    if not transcript:
        print("字幕取得に失敗")
        return False

    print(f"字幕取得成功: {len(transcript)} セグメント, 言語: {detected_lang}")

    # テキスト変換テスト
    text = format_transcript_text(transcript)
    print(f"テキスト変換成功: {len(text)} 文字")

    # プレビュー表示
    print("\n--- 字幕プレビュー (先頭200文字) ---")
    print(text[:200] + "..." if len(text) > 200 else text)
    print("--- プレビュー終了 ---")

    return True


if __name__ == "__main__":
    try:
        success = test_basic_functionality()
        if success:
            print("\nテスト成功! ハイブリッドツールが正常に動作します。")
        else:
            print("\nテスト失敗。設定を確認してください。")
    except Exception as e:
        print(f"\nテスト中にエラーが発生: {e}")
        import traceback

        traceback.print_exc()
