#!/usr/bin/env python3
"""
YouTubeTranscriptApiのインポート方法を修正するパッチ
"""

import re
from datetime import datetime
from pathlib import Path

APP_PATH = Path(r"C:\Users\Tenormusica\youtube_transcript_webapp\app_mobile.py")


def main():
    """メイン処理"""
    if not APP_PATH.exists():
        print(f"❌ ファイルが見つかりません: {APP_PATH}")
        return False

    src = APP_PATH.read_text(encoding="utf-8")

    # バックアップ作成
    backup = APP_PATH.with_suffix(
        APP_PATH.suffix + f".bak2-{datetime.now():%Y%m%d-%H%M%S}"
    )
    backup.write_text(src, encoding="utf-8")

    # インポート部分を修正
    old_import = "from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled"
    new_import = "from youtube_transcript_api import YouTubeTranscriptApi"

    if old_import in src:
        src = src.replace(old_import, new_import)
        print("✅ インポート文を修正しました")

    # get_transcript の使用方法を修正
    src = re.sub(
        r"data = YouTubeTranscriptApi\.get_transcript\(video_id, languages=\[l\]\)",
        r"data = YouTubeTranscriptApi.get_transcript(video_id, languages=[l])",
        src,
    )

    # NoTranscriptFound と TranscriptsDisabled の使用を修正
    src = re.sub(
        r"except NoTranscriptFound:",
        r'except Exception as e:\n                if "NoTranscriptFound" in str(type(e).__name__) or "could not retrieve" in str(e).lower():',
        src,
    )

    src = re.sub(
        r"except TranscriptsDisabled:",
        r'except Exception as e:\n                if "TranscriptsDisabled" in str(type(e).__name__) or "disabled" in str(e).lower():',
        src,
    )

    # ファイル保存
    APP_PATH.write_text(src, encoding="utf-8")

    print(f"✅ 修正完了: {APP_PATH}")
    print(f"🗂️  バックアップ: {backup.name}")
    return True


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 次のステップ:")
        print("1. サーバー再起動")
        print("2. 字幕抽出テスト実行")
    else:
        print("\n❌ パッチ適用に失敗しました")
