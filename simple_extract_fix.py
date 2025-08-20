#!/usr/bin/env python3
"""
簡単な字幕抽出関数の置換（確実に動作するバージョン）
"""

from datetime import datetime
from pathlib import Path

APP_PATH = Path(r"C:\Users\Tenormusica\youtube_transcript_webapp\app_mobile.py")

# 確実に動作する新しい関数
new_function = '''
def extract_youtube_transcript(video_url, language_code="ja"):
    """YouTube字幕抽出（シンプル確実版）"""
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

        # --- 言語リスト ---
        langs = []
        if language_code and language_code != "auto":
            langs.append(language_code)
        for l in ["ja", "en"]:
            if l not in langs:
                langs.append(l)

        # --- 直接APIを使用 ---
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
            except Exception as e:
                logger.warning(f"[extract] language {l} failed: {e}")
                continue

        # --- フォールバック: 利用可能な字幕を取得 ---
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            for t in transcripts:
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
                    logger.warning(f"[extract] fallback failed: {inner_e}")
                    continue
        except Exception as list_e:
            logger.warning(f"[extract] list_transcripts failed: {list_e}")

        raise ValueError("利用可能な字幕が見つかりませんでした")

    except Exception as e:
        logger.error(f"[extract] error: {e}")
        return {"success": False, "error": str(e)}
'''

def main():
    """メイン処理"""
    if not APP_PATH.exists():
        print(f"❌ ファイルが見つかりません: {APP_PATH}")
        return False

    src = APP_PATH.read_text(encoding="utf-8")
    
    # バックアップ作成
    backup = APP_PATH.with_suffix(APP_PATH.suffix + f".bak3-{datetime.now():%Y%m%d-%H%M%S}")
    backup.write_text(src, encoding="utf-8")
    
    # 既存の関数を検索して置換
    import re
    
    # 現在の関数ブロックを削除
    pattern = r'def extract_youtube_transcript\(video_url, language_code="ja"\):.*?(?=\n@app\.route\(|\nif __name__|\n\ndef |\Z)'
    
    new_src = re.sub(pattern, new_function.strip(), src, flags=re.DOTALL)
    
    if new_src != src:
        APP_PATH.write_text(new_src, encoding="utf-8")
        print(f"✅ 関数置換完了: {APP_PATH}")
        print(f"🗂️  バックアップ: {backup.name}")
        return True
    else:
        print("⚠️  関数ブロックが見つかりませんでした")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🚀 次のステップ:")
        print("1. サーバー再起動 (Ctrl+C → py -3 app_mobile.py)")
        print("2. 字幕抽出テスト実行")
    else:
        print("\n❌ パッチ適用に失敗しました")