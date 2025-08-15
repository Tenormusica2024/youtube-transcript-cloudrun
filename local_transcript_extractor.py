#!/usr/bin/env python3
"""
YouTube字幕抽出ツール (ローカル版)
GitHub Pages対応のシンプルな字幕抽出スクリプト
"""

import json
import re
import sys
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

try:
    from youtube_transcript_api import (NoTranscriptFound, TranscriptsDisabled,
                                        YouTubeTranscriptApi)
    from youtube_transcript_api.formatters import (JSONFormatter, SRTFormatter,
                                                   TextFormatter,
                                                   WebVTTFormatter)
except ImportError:
    print("❌ 必要なライブラリがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("pip install youtube-transcript-api")
    sys.exit(1)


def extract_video_id(url):
    """URLまたは動画IDから動画IDを抽出"""
    # 直接の動画IDの場合（11文字）
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url.strip()):
        return url.strip()

    try:
        parsed_url = urlparse(url.strip())

        # youtu.be format
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]

        # youtube.com format
        if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                params = parse_qs(parsed_url.query)
                return params.get("v", [None])[0]
            if parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            if parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]

        raise ValueError(f"Invalid YouTube URL: {url}")
    except Exception as e:
        print(f"❌ URL解析エラー: {e}")
        return None


def get_available_languages(video_id):
    """利用可能な字幕言語を取得"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        languages = []
        for transcript in transcript_list:
            languages.append(
                {
                    "code": transcript.language_code,
                    "name": transcript.language,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                }
            )
        return languages
    except Exception as e:
        print(f"⚠️ 字幕言語の取得に失敗: {e}")
        return []


def get_transcript(video_id, lang="ja"):
    """字幕を取得"""
    try:
        print(f"🎬 動画 {video_id} の字幕を抽出中...")

        # 利用可能な言語をチェック
        available_languages = get_available_languages(video_id)
        if available_languages:
            print("📋 利用可能な字幕言語:")
            for lang_info in available_languages:
                status = "🤖自動生成" if lang_info["is_generated"] else "👤手動作成"
                print(f"  - {lang_info['code']}: {lang_info['name']} ({status})")

        try:
            if lang == "auto":
                # 最初に利用可能な字幕を取得
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                detected_lang = "auto"
            else:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=[lang]
                )
                detected_lang = lang

            print(f"✅ {detected_lang} 字幕抽出成功: {len(transcript)} セグメント")
            return transcript, detected_lang

        except NoTranscriptFound:
            print(f"⚠️ {lang} 字幕が見つかりません。英語を試します...")
            try:
                transcript = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en"]
                )
                print(f"✅ 英語字幕抽出成功: {len(transcript)} セグメント")
                return transcript, "en"
            except NoTranscriptFound:
                print("❌ 日本語・英語の字幕が見つかりません")
                if available_languages:
                    # 利用可能な最初の言語を試す
                    first_lang = available_languages[0]["code"]
                    print(f"🔄 {first_lang} 字幕を試します...")
                    transcript = YouTubeTranscriptApi.get_transcript(
                        video_id, languages=[first_lang]
                    )
                    print(f"✅ {first_lang} 字幕抽出成功: {len(transcript)} セグメント")
                    return transcript, first_lang
                return None, None

    except TranscriptsDisabled:
        print("❌ この動画は字幕が無効になっています")
        return None, None
    except Exception as e:
        print(f"❌ 字幕抽出エラー: {e}")
        return None, None


def format_transcript(transcript, output_format="text"):
    """字幕をフォーマット"""
    if not transcript:
        return ""

    if output_format == "srt":
        formatter = SRTFormatter()
        return formatter.format_transcript(transcript)
    elif output_format == "vtt":
        formatter = WebVTTFormatter()
        return formatter.format_transcript(transcript)
    elif output_format == "json":
        formatter = JSONFormatter()
        return formatter.format_transcript(transcript)
    elif output_format == "raw":
        return " ".join([item["text"] for item in transcript])
    else:  # text/formatted
        raw_text = " ".join([item["text"] for item in transcript])
        return raw_text.replace("。", "。\n\n")


def create_simple_summary(text, max_sentences=5):
    """シンプルな要約を作成"""
    sentences = [s.strip() + "。" for s in text.split("。") if len(s.strip()) > 15]

    # 重要そうな文を選択（長めの文を優先）
    important_sentences = sorted(sentences, key=len, reverse=True)
    summary_sentences = important_sentences[
        : min(max_sentences, len(important_sentences))
    ]

    return " ".join(summary_sentences)


def save_results(
    video_id, youtube_url, language, output_format, content, transcript_data
):
    """結果をファイルに保存"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # テキストファイル保存
    filename = f"transcript_{video_id}_{int(time.time())}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"YouTube字幕抽出結果\n")
        f.write(f"{'='*50}\n")
        f.write(f"動画ID: {video_id}\n")
        f.write(f"URL: {youtube_url}\n")
        f.write(f"言語: {language}\n")
        f.write(f"形式: {output_format}\n")
        f.write(f"処理日時: {timestamp}\n")
        f.write(f"文字数: {len(content)}\n")
        f.write(f"セグメント数: {len(transcript_data)}\n")
        f.write(f"\n{'='*50}\n")
        f.write(f"内容:\n")
        f.write(f"{'='*50}\n")
        f.write(content)

        # 要約を追加
        if output_format != "summary_only":
            raw_text = " ".join([item["text"] for item in transcript_data])
            summary = create_simple_summary(raw_text)
            if summary:
                f.write(f"\n\n{'='*50}\n")
                f.write(f"要約:\n")
                f.write(f"{'='*50}\n")
                f.write(summary)

    # JSON形式でも保存
    json_filename = f"transcript_{video_id}_{int(time.time())}.json"
    result_data = {
        "video_id": video_id,
        "youtube_url": youtube_url,
        "language": language,
        "format": output_format,
        "timestamp": timestamp,
        "character_count": len(content),
        "segment_count": len(transcript_data),
        "content": content,
        "raw_transcript": transcript_data,
    }

    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    return filename, json_filename


def main():
    """メイン処理"""
    print("🎬 YouTube字幕抽出ツール")
    print("=" * 50)

    # YouTube URLまたは動画IDを入力
    while True:
        url_input = input("\n📺 YouTube URLまたは動画IDを入力してください: ").strip()
        if not url_input:
            print("❌ URLまたは動画IDを入力してください")
            continue

        video_id = extract_video_id(url_input)
        if video_id:
            break
        else:
            print("❌ 有効なYouTube URLまたは動画IDを入力してください")

    print(f"🆔 動画ID: {video_id}")

    # 言語選択
    print("\n🌐 字幕言語を選択してください:")
    languages = {
        "1": ("ja", "日本語"),
        "2": ("en", "英語"),
        "3": ("ko", "韓国語"),
        "4": ("zh", "中国語"),
        "5": ("es", "スペイン語"),
        "6": ("fr", "フランス語"),
        "7": ("de", "ドイツ語"),
        "8": ("auto", "自動検出"),
    }

    for key, (code, name) in languages.items():
        print(f"  {key}: {name} ({code})")

    while True:
        lang_choice = input("選択 (1-8, デフォルト=1): ").strip() or "1"
        if lang_choice in languages:
            selected_lang, lang_name = languages[lang_choice]
            break
        print("❌ 1-8の数字を入力してください")

    print(f"🔤 選択された言語: {lang_name} ({selected_lang})")

    # 出力形式選択
    print("\n📄 出力形式を選択してください:")
    formats = {
        "1": ("text", "プレーンテキスト"),
        "2": ("srt", "SRT字幕ファイル"),
        "3": ("vtt", "WebVTT字幕ファイル"),
        "4": ("json", "JSON形式"),
        "5": ("raw", "Raw形式（改行なし）"),
    }

    for key, (code, name) in formats.items():
        print(f"  {key}: {name}")

    while True:
        format_choice = input("選択 (1-5, デフォルト=1): ").strip() or "1"
        if format_choice in formats:
            selected_format, format_name = formats[format_choice]
            break
        print("❌ 1-5の数字を入力してください")

    print(f"📋 選択された形式: {format_name}")

    # 字幕抽出実行
    print(f"\n🚀 字幕抽出を開始します...")
    transcript, detected_lang = get_transcript(video_id, selected_lang)

    if not transcript:
        print("❌ 字幕の抽出に失敗しました")
        return

    # フォーマット処理
    print("🔧 字幕をフォーマット中...")
    formatted_content = format_transcript(transcript, selected_format)

    # 結果保存
    print("💾 結果を保存中...")
    text_file, json_file = save_results(
        video_id,
        url_input,
        detected_lang,
        selected_format,
        formatted_content,
        transcript,
    )

    # 結果表示
    print(f"\n✅ 字幕抽出完了!")
    print(f"📊 文字数: {len(formatted_content):,} 文字")
    print(f"📋 セグメント数: {len(transcript)} セグメント")
    print(f"🌐 検出言語: {detected_lang}")
    print(f"📄 保存ファイル: {text_file}")
    print(f"📊 JSON形式: {json_file}")

    # プレビュー表示
    if selected_format in ["text", "raw"]:
        print(f"\n📖 プレビュー (先頭300文字):")
        print("-" * 50)
        preview = (
            formatted_content[:300] + "..."
            if len(formatted_content) > 300
            else formatted_content
        )
        print(preview)
        print("-" * 50)

    print(f"\n🎉 処理完了! ファイルをご確認ください。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 処理を中断しました。")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
