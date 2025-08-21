#!/usr/bin/env python3
"""
ハイブリッド字幕抽出ツールのデモ実行
自動でサンプル動画の字幕を抽出・AI要約します
"""

import os
import sys

# 現在のディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hybrid_transcript_tool import (CLOUD_RUN_API_URL, extract_video_id,
                                    format_transcript_text,
                                    get_transcript_local, save_results,
                                    send_to_api_for_formatting)


def demo_run():
    """デモ実行"""
    print("YouTube字幕抽出ツール（ハイブリッド版）- デモ実行")
    print("=" * 60)
    print("ローカル抽出 + Cloud Run AI整形・要約")
    print("=" * 60)

    # サンプル動画URL (短い動画)
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    print(f"\nデモ用YouTube URL: {test_url}")

    # 動画ID抽出
    video_id = extract_video_id(test_url)
    print(f"動画ID: {video_id}")

    if not video_id:
        print("動画ID抽出に失敗しました")
        return False

    # 字幕抽出設定
    lang = "auto"  # 自動検出
    api_url = CLOUD_RUN_API_URL  # Cloud Run API使用

    print(f"選択された言語: 自動検出 ({lang})")
    print(f"使用するAPI: {api_url}")

    # 字幕抽出実行
    print("\n字幕抽出を開始します...")
    transcript, detected_lang = get_transcript_local(video_id, lang)

    if not transcript:
        print("字幕の抽出に失敗しました")
        return False

    # プレーンテキストに変換
    transcript_text = format_transcript_text(transcript)
    print(f"字幕テキスト取得完了: {len(transcript_text)} 文字")

    # API経由でAI整形・要約
    formatted_text, summary = send_to_api_for_formatting(
        transcript_text, api_url, detected_lang
    )

    # 結果保存
    print("結果を保存中...")
    text_file, json_file = save_results(
        video_id, test_url, detected_lang, formatted_text, summary, transcript
    )

    # 結果表示
    print(f"\n処理完了!")
    print(f"文字数: {len(formatted_text):,} 文字")
    print(f"セグメント数: {len(transcript)} セグメント")
    print(f"検出言語: {detected_lang}")
    print(f"保存ファイル: {text_file}")
    print(f"JSON形式: {json_file}")
    print(f"AI要約: {'あり' if summary else 'なし'}")

    # プレビュー表示
    print(f"\nAI整形済みプレビュー (先頭500文字):")
    print("-" * 60)
    preview = (
        formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text
    )
    print(preview)
    print("-" * 60)

    if summary:
        print(f"\nAI要約プレビュー (先頭300文字):")
        print("-" * 60)
        summary_preview = summary[:300] + "..." if len(summary) > 300 else summary
        print(summary_preview)
        print("-" * 60)

    print(f"\n処理完了! ファイルをご確認ください。")
    return True


if __name__ == "__main__":
    try:
        success = demo_run()
        if success:
            print("\nデモ実行成功! ハイブリッドツールが正常に動作しました。")
        else:
            print("\nデモ実行失敗。設定を確認してください。")
    except Exception as e:
        print(f"\nデモ実行中にエラーが発生: {e}")
        import traceback

        traceback.print_exc()
