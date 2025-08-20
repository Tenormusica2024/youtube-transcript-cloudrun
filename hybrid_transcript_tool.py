#!/usr/bin/env python3
"""
YouTube字幕抽出ツール（ハイブリッド版）
- ローカル抽出 + Cloud Run API要約機能
- スタンドアロンHTMLページ対応
"""

import json
import re
import requests
import sys
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

try:
    from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
    from youtube_transcript_api.formatters import SRTFormatter, WebVTTFormatter, JSONFormatter, TextFormatter
except ImportError:
    print("必要なライブラリがインストールされていません。")
    print("以下のコマンドでインストールしてください:")
    print("pip install youtube-transcript-api")
    sys.exit(1)

# Cloud Run API設定
CLOUD_RUN_API_URL = "https://yt-transcript-ycqe3vmjva-uc.a.run.app"
DEFAULT_LOCAL_URL = "http://localhost:8080"

def extract_video_id(url):
    """URLまたは動画IDから動画IDを抽出"""
    # 直接の動画IDの場合（11文字）
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url.strip()):
        return url.strip()
    
    try:
        parsed_url = urlparse(url.strip())
        
        # youtu.be format
        if parsed_url.hostname == 'youtu.be':
            return parsed_url.path[1:]
        
        # youtube.com format
        if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
            if parsed_url.path == '/watch':
                params = parse_qs(parsed_url.query)
                return params.get('v', [None])[0]
            if parsed_url.path.startswith('/embed/'):
                return parsed_url.path.split('/')[2]
            if parsed_url.path.startswith('/v/'):
                return parsed_url.path.split('/')[2]
        
        raise ValueError(f"Invalid YouTube URL: {url}")
    except Exception as e:
        print(f"URL解析エラー: {e}")
        return None

def get_transcript_local(video_id, lang='ja'):
    """ローカルで字幕を取得"""
    try:
        print(f"動画 {video_id} の字幕をローカルで抽出中...")
        
        # 複数言語を試行
        languages_to_try = []
        if lang == 'auto':
            languages_to_try = ['ja', 'en', 'ko', 'zh', 'es', 'fr', 'de']
        else:
            languages_to_try = [lang, 'en', 'ja']
        
        # youtube-transcript-api 1.2.2 の新しいAPIを使用
        try:
            api = YouTubeTranscriptApi()
            
            # 利用可能な字幕リストを取得
            transcript_list = api.list(video_id)
            
            # 希望する言語を試行
            for try_lang in languages_to_try:
                try:
                    for transcript_info in transcript_list:
                        if transcript_info.language_code == try_lang:
                            fetched_transcript = transcript_info.fetch()
                            transcript = fetched_transcript.to_raw_data()
                            print(f"{try_lang} 字幕抽出成功: {len(transcript)} セグメント")
                            return transcript, try_lang
                except:
                    continue
            
            # 最初に利用可能な字幕を取得
            for transcript_info in transcript_list:
                try:
                    fetched_transcript = transcript_info.fetch()
                    transcript = fetched_transcript.to_raw_data()
                    detected_lang = transcript_info.language_code
                    print(f"{detected_lang} 字幕抽出成功: {len(transcript)} セグメント")
                    return transcript, detected_lang
                except:
                    continue
            
            return None, None
            
        except Exception as e:
            print(f"API初期化エラー: {e}")
            return None, None
                
    except TranscriptsDisabled:
        print("この動画は字幕が無効になっています")
        return None, None
    except Exception as e:
        print(f"字幕抽出エラー: {e}")
        return None, None

def format_transcript_text(transcript):
    """字幕をプレーンテキストに変換"""
    if not transcript:
        return ""
    return " ".join([item['text'] for item in transcript])

def send_to_api_for_formatting(transcript_text, api_url, lang='ja'):
    """APIサーバーに字幕テキストを送信してGemini AI整形・要約を実行"""
    try:
        print(f"AIで整形・要約中... (サーバー: {api_url})")
        
        # ヘルスチェック
        try:
            health_response = requests.get(f"{api_url}/health", timeout=10)
            if health_response.status_code != 200:
                raise requests.RequestException("Health check failed")
            print("APIサーバー接続確認")
        except:
            print(f"APIサーバー {api_url} に接続できません")
            return transcript_text, ""
        
        # 字幕テキストを送信
        payload = {
            "transcript_text": transcript_text,
            "lang": lang,
            "format": "txt"
        }
        
        response = requests.post(
            f"{api_url}/extract",
            json=payload,
            timeout=120,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                formatted_text = result.get('formatted_transcript', transcript_text)
                summary = result.get('summary', '')
                print(f"AI整形・要約完了")
                return formatted_text, summary
            else:
                print(f"API処理エラー: {result.get('error', 'Unknown error')}")
                return transcript_text, ""
        else:
            print(f"APIリクエストエラー: {response.status_code}")
            return transcript_text, ""
            
    except Exception as e:
        print(f"API通信エラー: {e}")
        return transcript_text, ""

def save_results(video_id, youtube_url, language, formatted_content, summary, transcript_data):
    """結果をファイルに保存"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # テキストファイル保存
    filename = f"transcript_{video_id}_{int(time.time())}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"YouTube字幕抽出結果（ハイブリッド版）\n")
        f.write(f"{'='*60}\n")
        f.write(f"動画ID: {video_id}\n")
        f.write(f"URL: {youtube_url}\n")
        f.write(f"言語: {language}\n")
        f.write(f"処理日時: {timestamp}\n")
        f.write(f"文字数: {len(formatted_content)}\n")
        f.write(f"セグメント数: {len(transcript_data)}\n")
        f.write(f"\n{'='*60}\n")
        f.write(f"AI整形済み字幕:\n")
        f.write(f"{'='*60}\n")
        f.write(formatted_content)
        
        # 要約があれば追加
        if summary:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"AI要約:\n")
            f.write(f"{'='*60}\n")
            f.write(summary)
    
    # JSON形式でも保存
    json_filename = f"transcript_{video_id}_{int(time.time())}.json"
    result_data = {
        'video_id': video_id,
        'youtube_url': youtube_url,
        'language': language,
        'timestamp': timestamp,
        'character_count': len(formatted_content),
        'segment_count': len(transcript_data),
        'formatted_content': formatted_content,
        'summary': summary,
        'raw_transcript': transcript_data
    }
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return filename, json_filename

def main():
    """メイン処理"""
    print("YouTube字幕抽出ツール（ハイブリッド版）")
    print("="*60)
    print("ローカル抽出 + Cloud Run AI整形・要約")
    print("="*60)
    
    # YouTube URLまたは動画IDを入力
    while True:
        url_input = input("\nYouTube URLまたは動画IDを入力してください: ").strip()
        if not url_input:
            print("URLまたは動画IDを入力してください")
            continue
        
        video_id = extract_video_id(url_input)
        if video_id:
            break
        else:
            print("有効なYouTube URLまたは動画IDを入力してください")
    
    print(f"動画ID: {video_id}")
    
    # 言語選択
    print("\n字幕言語を選択してください:")
    languages = {
        '1': ('ja', '日本語'),
        '2': ('en', '英語'),
        '3': ('ko', '韓国語'),
        '4': ('zh', '中国語'),
        '5': ('es', 'スペイン語'),
        '6': ('fr', 'フランス語'),
        '7': ('de', 'ドイツ語'),
        '8': ('auto', '自動検出')
    }
    
    for key, (code, name) in languages.items():
        print(f"  {key}: {name} ({code})")
    
    while True:
        lang_choice = input("選択 (1-8, デフォルト=1): ").strip() or '1'
        if lang_choice in languages:
            selected_lang, lang_name = languages[lang_choice]
            break
        print("1-8の数字を入力してください")
    
    print(f"選択された言語: {lang_name} ({selected_lang})")
    
    # APIサーバー選択
    print("\nAPIサーバーを選択してください:")
    api_options = {
        '1': (CLOUD_RUN_API_URL, 'Cloud Run (推奨)'),
        '2': (DEFAULT_LOCAL_URL, 'ローカルサーバー'),
        '3': ('custom', 'カスタムURL')
    }
    
    for key, (url, name) in api_options.items():
        print(f"  {key}: {name}")
    
    while True:
        api_choice = input("選択 (1-3, デフォルト=1): ").strip() or '1'
        if api_choice in api_options:
            if api_choice == '3':
                api_url = input("カスタムAPIのURLを入力してください: ").strip()
                if not api_url:
                    print("URLを入力してください")
                    continue
            else:
                api_url, _ = api_options[api_choice]
            break
        print("1-3の数字を入力してください")
    
    print(f"使用するAPI: {api_url}")
    
    # 字幕抽出実行
    print(f"\n字幕抽出を開始します...")
    transcript, detected_lang = get_transcript_local(video_id, selected_lang)
    
    if not transcript:
        print("字幕の抽出に失敗しました")
        return
    
    # プレーンテキストに変換
    transcript_text = format_transcript_text(transcript)
    print(f"字幕テキスト取得完了: {len(transcript_text)} 文字")
    
    # API経由でAI整形・要約
    formatted_text, summary = send_to_api_for_formatting(transcript_text, api_url, detected_lang)
    
    # 結果保存
    print("結果を保存中...")
    text_file, json_file = save_results(
        video_id, url_input, detected_lang, 
        formatted_text, summary, transcript
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
    print(f"\nAI整形済みプレビュー (先頭300文字):")
    print("-" * 60)
    preview = formatted_text[:300] + "..." if len(formatted_text) > 300 else formatted_text
    print(preview)
    print("-" * 60)
    
    if summary:
        print(f"\nAI要約プレビュー (先頭200文字):")
        print("-" * 60)
        summary_preview = summary[:200] + "..." if len(summary) > 200 else summary
        print(summary_preview)
        print("-" * 60)
    
    print(f"\n処理完了! ファイルをご確認ください。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n処理を中断しました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()