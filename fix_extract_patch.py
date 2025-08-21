# -*- coding: utf-8 -*-
"""
app_mobile.py の extract_youtube_transcript 関数を
YouTubeTranscriptApi の正式API(get_transcript/list_transcripts)を使う堅牢版に置換します。
- 置換前に .bak-YYYYMMDD-HHMMSS でバックアップを作成
- 正規表現で関数ブロックを安全に差し替え
"""

import re
from datetime import datetime
from pathlib import Path

APP_PATH = Path(r"C:\Users\Tenormusica\youtube_transcript_webapp\app_mobile.py")

replacement = r'''
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled

def extract_youtube_transcript(video_url, language_code="ja"):
    """YouTube字幕抽出（Shorts対応＆堅牢フォールバック）"""
    try:
        # --- 動画ID抽出 ---
        parsed_url = urlparse(video_url)
        video_id = None
        if "youtube.com" in parsed_url.netloc or "m.youtube.com" in parsed_url.netloc:
            if parsed_url.path == "/watch":
                video_id = parse_qs(parsed_url.query).get("v", [None])[0]
            elif parsed_url.path.startswith("/shorts/"):
                video_id = parsed_url.path.split("/shorts/")[1].split("?")[0]
            elif parsed_url.path.startswith("/embed/"):
                video_id = parsed_url.path.split("/embed/")[1].split("?")[0]
            elif parsed_url.path.startswith("/v/"):
                video_id = parsed_url.path.split("/v/")[1].split("?")[0]
        elif "youtu.be" in parsed_url.netloc:
            video_id = parsed_url.path.lstrip("/").split("?")[0]

        if not video_id:
            raise ValueError("有効なYouTube URLではありません")

        video_id = video_id.split("&")[0]
        logger.info(f"[extract] video_id={video_id}")

        # --- 言語フォールバック順 ---
        langs = []
        if language_code and language_code != "auto":
            langs.append(language_code)
        for l in ["ja", "en"]:
            if l not in langs:
                langs.append(l)

        # --- 正式API: get_transcript を優先 ---
        for l in langs:
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=[l])
                full_text = " ".join([item["text"] for item in data])
                return {
                    "success": True,
                    "transcript": full_text,
                    "language": l,
                    "video_id": video_id,
                }
            except NoTranscriptFound:
                continue
            except TranscriptsDisabled:
                raise ValueError("この動画の字幕は無効化されています")

        # --- まだダメなら list_transcripts で取得可能なものを拾う ---
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            preferred = [t for t in transcripts if getattr(t, "language_code", None) in ("ja","en")]
            ordered = preferred + [t for t in transcripts if t not in preferred]
            for t in ordered:
                try:
                    data = t.fetch()
                    full_text = " ".join([item["text"] for item in data])
                    return {
                        "success": True,
                        "transcript": full_text,
                        "language": getattr(t, "language_code", "unknown"),
                        "video_id": video_id,
                    }
                except Exception as inner_e:
                    logger.warning(f"[extract] fallback fetch failed: {inner_e}")
                    continue
        except Exception as list_e:
            logger.warning(f"[extract] list_transcripts failed: {list_e}")

        raise ValueError("利用可能な字幕が見つかりませんでした")

    except Exception as e:
        logger.error(f"[extract] error: {e}")
        return {"success": False, "error": str(e)}
'''.lstrip(
    "\n"
)


def main():
    if not APP_PATH.exists():
        print(f"❌ ファイルが見つかりません: {APP_PATH}")
        return

    src = APP_PATH.read_text(encoding="utf-8")

    # def extract_youtube_transcript(...) から次の @app.route( または if __name__ == "__main__": の直前までを置換
    pattern = r'(?ms)def\s+extract_youtube_transcript\([^)]*\):\s*.*?(?=^\s*@app\.route\(|^\s*if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:)'

    if not re.search(pattern, src):
        print(
            "⚠️  既存の関数ブロックを特定できませんでした。ファイル末尾に新定義を追記します。"
        )
        # 追記（最悪ケースでも新関数を提供）
        backup = APP_PATH.with_suffix(
            APP_PATH.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}"
        )
        backup.write_text(src, encoding="utf-8")
        APP_PATH.write_text(src.rstrip() + "\n\n" + replacement, encoding="utf-8")
        print(f"✅ バックアップ作成: {backup.name}")
        print(
            "✅ 新しい関数を末尾に追記しました（ルートは既存のままでも extract_* を呼んでいれば有効）"
        )
        return

    # 正常置換
    new_src = re.sub(pattern, replacement, src)
    if new_src == src:
        print("⚠️  置換が発生しませんでした（差分なし）。")
        return

    # バックアップ＆保存
    backup = APP_PATH.with_suffix(
        APP_PATH.suffix + f".bak-{datetime.now():%Y%m%d-%H%M%S}"
    )
    backup.write_text(src, encoding="utf-8")
    APP_PATH.write_text(new_src, encoding="utf-8")

    print(f"✅ 置換完了: {APP_PATH}")
    print(f"🗂️  バックアップ: {backup.name}")


if __name__ == "__main__":
    main()
