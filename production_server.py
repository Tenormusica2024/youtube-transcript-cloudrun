#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import threading
import time
import webbrowser
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# UTF-8設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Gemini AI要約関数
def generate_gemini_summary(text, video_id, language):
    """
    Gemini APIを使用してYouTube字幕のAI要約を生成
    """
    try:
        # Gemini APIキーの設定確認
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            print("[WARN] GEMINI_API_KEY not found in environment")
            return generate_fallback_summary(text, video_id, language)
        
        # Gemini APIの初期化
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 詳細要約用プロンプト（3倍長く）
        prompt = f"""
以下はYouTube動画の字幕テキストです。この内容を日本語で詳細に要約してください。

**詳細要約条件:**
1. 動画の全体構成を把握し、段階的に要約する
2. 主要なポイントを漏らさず、詳細に説明する
3. 具体的な数字、事例、引用があれば含める
4. 動画の背景・文脈・意図も推察して記載する
5. 視聴者にとって価値ある詳細情報を重視する
6. 10-15文程度の充実した要約を作成する
7. 各セクションごとに見出しをつけて構造化する

**字幕テキスト:**
{text[:4000]}{'...' if len(text) > 4000 else ''}

**詳細AI要約:**
        """
        
        # Gemini APIで要約生成
        response = model.generate_content(prompt)
        
        if response and response.text:
            summary = response.text.strip()
            # AI要約テキストの可読性向上（句点での改行）
            formatted_summary = format_summary_text(summary)
            print(f"[OK] Gemini summary generated: {len(summary)} characters")
            return f"""🤖 AI要約 (Gemini 1.5 Flash):

{formatted_summary}

---
📊 分析情報:
・ 動画ID: {video_id}
・ 元テキスト文字数: {len(text):,}文字
・ 処理時刻: {time.strftime('%H:%M:%S')}
・ 言語設定: {language.upper()}"""
        else:
            print("[WARN] Gemini API returned empty response")
            return generate_fallback_summary(text, video_id, language)
            
    except Exception as e:
        print(f"[ERROR] Gemini API error: {str(e)}")
        return generate_fallback_summary(text, video_id, language)

def generate_fallback_summary(text, video_id, language):
    """
    Gemini APIが使用できない場合の詳細フォールバック要約
    """
    # より詳細なキーワード抽出と文章要約
    sentences = text.replace('。', '。\n').split('\n')
    important_sentences = [s.strip() for s in sentences if len(s.strip()) > 15][:8]  # より多くの文を抽出
    
    # 文字数による分析
    char_count = len(text)
    sentence_count = len([s for s in sentences if s.strip()])
    
    return f"""📝 詳細基本要約 (Fallback):

## 主要な内容:
・ {important_sentences[0] if len(important_sentences) > 0 else '情報なし'}

・ {important_sentences[1] if len(important_sentences) > 1 else ''}

・ {important_sentences[2] if len(important_sentences) > 2 else ''}

・ {important_sentences[3] if len(important_sentences) > 3 else ''}

## 補足情報:
・ {important_sentences[4] if len(important_sentences) > 4 else ''}

・ {important_sentences[5] if len(important_sentences) > 5 else ''}

・ {important_sentences[6] if len(important_sentences) > 6 else ''}

・ {important_sentences[7] if len(important_sentences) > 7 else ''}

---
📊 詳細統計情報:
・ 動画ID: {video_id}
・ 元テキスト文字数: {char_count:,}文字
・ 推定文数: {sentence_count}文
・ 平均文長: {char_count//max(sentence_count, 1)}文字/文
・ 処理言語: {language.upper()}
・ 要約方式: 基本抽出型
・ 状態: Gemini API未設定

⚠️ GEMINI_API_KEYを設定すると、AI分析による高品質で構造化された詳細要約が利用できます。"""

# 高度なテキスト整形関数（メモリバンク最新版適用）
def format_transcript_text(original_text):
    """
    YouTube字幕テキストを最高品質で整形する
    過去のプロジェクト実績とメモリバンクの知見を統合した最新版
    """
    import re
    
    if not original_text or not original_text.strip():
        return original_text
    
    text = original_text
    
    # Phase 1: 基本的なクリーニング
    # 不要な記号や文字の除去
    text = re.sub(r'[\u266a\u266b\u266c\u266d\u266e\u266f]', '', text)  # 音楽記号削除
    text = re.sub(r'\[音楽\]|\[Music\]|\[♪\]', '', text)
    text = re.sub(r'^\s*[\[\(].*?[\]\)]\s*', '', text, flags=re.MULTILINE)  # [拍手]等の除去
    
    # Phase 2: 話題区切り重視の適度な改行処理（日英両対応）
    # 話題転換を示すキーワードでの改行
    topic_change_keywords = [
        # 話題転換の日本語キーワード
        'さて', 'ところで', 'それでは', 'では', '次に', '続いて', 'まず', '最初に', '最後に',
        'それから', 'その後', '一方で', '他方', '反対に', '逆に', 'しかし', 'ただし', 'でも',
        'また', 'さらに', 'そして', 'それに', '加えて', 'なお', 'ちなみに',
        # 英語の話題転換
        'Now', 'However', 'Meanwhile', 'Furthermore', 'Moreover', 'Additionally', 
        'On the other hand', 'In contrast', 'Nevertheless', 'Therefore', 'Consequently',
        'First', 'Second', 'Third', 'Finally', 'Next', 'Then', 'After that'
    ]
    
    for keyword in topic_change_keywords:
        # 話題転換キーワードの前に空行を追加
        text = re.sub(f'([。！？.!?])\\s*{keyword}', f'\\1\n\n{keyword}', text)
        text = re.sub(f'\\s+{keyword}', f'\n\n{keyword}', text)
    
    # 長い文の区切りポイントでの適度な改行
    text = re.sub(r'([。！？])(\s*)([あ-んア-ン一-龯])', r'\1\2\3', text)  # 句点後は基本的に続ける
    text = re.sub(r'([.!?])(\s*)([A-Za-z])', r'\1\2\3', text)  # 英語も基本的に続ける
    
    # Phase 3: 高度な誤変換修正（拡張版）
    corrections = {
        # 敬語・丁寧語の修正
        '有り難う': 'ありがとう', '有難う': 'ありがとう',
        '宜しく': 'よろしく', '宜しい': 'よろしい',
        '御座います': 'ございます', '下さい': 'ください',
        '致します': 'いたします', '御願い': 'お願い',
        
        # よくある変換ミス
        '出来る': 'できる', '出来ます': 'できます', '出来ません': 'できません',
        '何時': 'いつ', '何処': 'どこ', '何故': 'なぜ', '如何': 'いかが',
        '沢山': 'たくさん', '一杯': 'いっぱい', '大分': 'だいぶ',
        '丁寧': 'ていねい', '綺麗': 'きれい', '奇麗': 'きれい',
        '美味しい': 'おいしい', '素晴らしい': 'すばらしい',
        
        # 技術系・現代語の修正
        'アプリケーション': 'アプリ', 'コミュニケーション': 'コミュニケ',
        'インターネット': 'ネット', 'コンピューター': 'コンピュータ',
        'データベース': 'DB', 'プログラミング': 'プログラム',
        
        # 口語・話し言葉の自然化
        'っていうか': 'というか', 'みたいな': 'のような',
        'やっぱり': 'やはり', 'めっちゃ': 'とても',
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # Phase 4: 接続詞・転換語での段落分け（大幅拡張）
    connectives = [
        # 順接
        'そして', 'それから', 'そうして', 'そこで', 'すると',
        # 逆接
        'しかし', 'ところが', 'けれども', 'だが', 'でも', 'ただし',
        # 添加
        'また', 'さらに', 'そのうえ', 'しかも', 'その他',
        # 対比
        '一方', '他方', 'これに対して', '逆に',
        # 理由・結果
        'なぜなら', 'というのは', 'だから', 'そのため', 'したがって', 'つまり',
        # 転換
        'ところで', 'さて', 'それでは', 'では', 'いずれにせよ',
        # 補足・例示
        'たとえば', 'つまり', 'すなわち', '具体的には',
        # 英語接続詞
        'However', 'Therefore', 'Moreover', 'Furthermore', 'Meanwhile',
        'For example', 'In addition', 'On the other hand'
    ]
    
    for conn in connectives:
        # 可読性重視の段落分けのための処理 - より多くの空行
        text = re.sub(f'([。！？])\\s*{conn}', f'\\1\n\n\n{conn}', text)  # 接続詞前に空行追加
        text = re.sub(f'\\s+{conn}', f'\n\n\n{conn}', text)  # 接続詞前に十分な空行
    
    # Phase 5: 高度な段落構造化
    lines = text.split('\n')
    structured_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        
        # 文の長さと内容による段落判定
        is_long_sentence = len(line) > 60
        is_complete_sentence = any(line.endswith(end) for end in ['。', '！', '？', '.', '!', '?'])
        is_important_point = any(keyword in line for keyword in ['重要', '注意', 'ポイント', '結論', '要点'])
        is_list_item = line.startswith(('・', '1.', '2.', '3.', '-', '*'))
        
        structured_lines.append(line)
        
        # 可読性重視の段落区切りの条件 - より多くの空行
        if is_complete_sentence:  # 全ての完結文の後に空行
            if i < len(lines) - 1:  # 最後の行でなければ
                structured_lines.append('')  # 空行追加
                if (is_long_sentence or is_important_point):  # 長文・重要文は更に空行
                    structured_lines.append('')  # 追加空行
        elif is_list_item:
            # リスト項目も空行で区切り
            structured_lines.append('')
    
    # Phase 6: 最終整形と品質向上
    formatted = '\n'.join(structured_lines)
    
    # 可読性重視の空行整理（より寛容に）
    formatted = re.sub(r'\n{6,}', '\n\n\n\n\n', formatted)  # 連続空行は最大5つまで
    formatted = re.sub(r'^\n+', '', formatted)  # 先頭の空行削除
    formatted = re.sub(r'\n+$', '', formatted)  # 末尾の空行削除
    
    # 文頭・行頭の整理
    formatted = re.sub(r'^[\s　]+', '', formatted, flags=re.MULTILINE)
    
    # 読みやすさ向上のための微調整
    formatted = re.sub(r'([。！？])([あ-んア-ン一-龯])', r'\1 \2', formatted)  # 句読点後にスペース
    
    return formatted.strip()

def format_summary_text(summary_text):
    """
    AI要約テキストの可読性向上（句点での改行処理）
    """
    import re
    
    if not summary_text or not summary_text.strip():
        return summary_text
    
    text = summary_text
    
    # 句点での改行処理（日本語・英語対応）
    # 日本語の句点（。）後に改行を追加
    text = re.sub(r'([。])([あ-んア-ン一-龯A-Za-z0-9])', r'\1\n\2', text)
    
    # 英語の句点（.）後に改行を追加（ただし数字や省略形は除外）
    text = re.sub(r'(\.)(\s+)([A-Z])', r'\1\n\2\3', text)
    
    # 感嘆符・疑問符の後にも改行を追加
    text = re.sub(r'([！？!?])([あ-んア-ン一-龯A-Za-z])', r'\1\n\2', text)
    
    # 箇条書きや見出しの前に適切な空行を追加
    text = re.sub(r'(\n)([・•\-\*1-9]\.?\s)', r'\1\n\2', text)
    text = re.sub(r'(\n)(#{1,6}\s)', r'\1\n\2', text)
    
    # 連続する空行を整理（最大2行まで）
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 先頭・末尾の空行を削除
    text = text.strip()
    
    return text

# 必要なライブラリのインストール確認とインポート
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("[OK] youtube-transcript-api imported successfully")
except ImportError as e:
    print(f"[WARN] youtube-transcript-api not found: {e}")
    print("[INFO] Installing youtube-transcript-api...")
    os.system('pip install youtube-transcript-api --upgrade')
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        print("[OK] youtube-transcript-api installed and imported")
    except Exception as install_error:
        print(f"[ERROR] Failed to install: {install_error}")

try:
    import google.generativeai as genai
    print("[OK] google-generativeai imported successfully")
except ImportError:
    print("[WARN] google-generativeai not found, installing...")
    os.system('pip install google-generativeai')

app = Flask(__name__)

# より詳細なCORS設定
CORS(app, 
     origins=['http://127.0.0.1:8087', 'http://localhost:8087'],
     methods=['GET', 'POST', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# プリフライトリクエストの処理
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        print("[INFO] Handling preflight OPTIONS request")
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

# テンプレートの自動リロード設定
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def extract():
    try:
        import re
        import time
        from datetime import datetime
        
        print(f"[INFO] ==== API REQUEST RECEIVED ====")
        print(f"[INFO] Request method: {request.method}")
        print(f"[INFO] Request headers: {dict(request.headers)}")
        print(f"[INFO] Request content type: {request.content_type}")
        
        data = request.get_json()
        print(f"[INFO] Request JSON data: {data}")
        
        url = data.get('url', '') if data else ''
        lang = data.get('lang', 'ja') if data else 'ja'
        generate_summary = data.get('generate_summary', True) if data else True
        
        print(f"[INFO] Extracted parameters - URL: {url}, Lang: {lang}, Summary: {generate_summary}")
        
        if not url:
            print(f"[ERROR] No URL provided")
            return jsonify({'success': False, 'error': 'URLを入力してください'})
        
        # YouTube URL解析
        video_id = None
        url_patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/|youtube\.com/shorts/)([a-zA-Z0-9_-]+)',
            r'^([a-zA-Z0-9_-]{11})$'  # 直接ID
        ]
        
        for pattern in url_patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                break
        
        if not video_id:
            return jsonify({'success': False, 'error': '有効なYouTube URLを入力してください'})
        
        print(f"[INFO] Extracting transcript for video ID: {video_id}")
        
        # 字幕取得
        try:
            # 正しいAPIメソッド（インスタンスメソッド）を使用
            api = YouTubeTranscriptApi()
            transcript = api.fetch(video_id, languages=[lang])
            print(f"[OK] Transcript fetched successfully: {len(transcript)} segments")
        except Exception as transcript_error:
            print(f"[ERROR] Transcript fetch failed: {str(transcript_error)}")
            # フォールバック: 言語指定なしで再試行
            try:
                print("[INFO] Retrying without language specification...")
                api = YouTubeTranscriptApi()
                transcript = api.fetch(video_id)
                print(f"[OK] Transcript fetched successfully (fallback): {len(transcript)} segments")
            except Exception as fallback_error:
                print(f"[ERROR] Fallback also failed: {str(fallback_error)}")
                return jsonify({
                    'success': False, 
                    'error': f'字幕を取得できませんでした: {str(transcript_error)} | Fallback: {str(fallback_error)}'
                })
        
        # テキスト整形
        if not transcript:
            return jsonify({'success': False, 'error': '字幕データが空です'})
        
        try:
            # FetchedTranscriptSnippetオブジェクトからテキストを抽出
            if hasattr(transcript[0], 'text'):
                original_text = ' '.join([snippet.text for snippet in transcript])
                print(f"[OK] Text extracted using .text attribute")
            elif isinstance(transcript[0], dict) and 'text' in transcript[0]:
                original_text = ' '.join([snippet['text'] for snippet in transcript])
                print(f"[OK] Text extracted using dict access")
            else:
                print(f"[WARN] Unknown transcript format: {type(transcript[0])}")
                original_text = ' '.join([str(snippet) for snippet in transcript])
        except Exception as text_error:
            print(f"[ERROR] Text extraction failed: {text_error}")
            original_text = str(transcript)[:500] + '...'
        
        if not original_text.strip():
            return jsonify({'success': False, 'error': '字幕テキストが取得できませんでした'})
        
        # 高度なテキスト整形処理
        formatted_text = format_transcript_text(original_text)
        
        print(f"[INFO] Text formatting completed: {len(original_text)} -> {len(formatted_text)} characters")
        
        # Gemini AI要約処理
        if generate_summary:
            summary_text = generate_gemini_summary(original_text, video_id, lang)
        else:
            summary_text = f"AI要約はリクエストされていません。"
        
        response = jsonify({
            'success': True,
            'title': f'YouTube動画 (ID: {video_id})',
            'transcript': formatted_text,
            'original_transcript': original_text,
            'summary': summary_text,
            'stats': {
                'segments': len(transcript),
                'characters': len(original_text),
                'language': lang.upper(),
                'video_id': video_id,
                'transcript_type': str(type(transcript[0]).__name__ if transcript else 'Unknown')
            },
            'version': f'v1.3.11-production-{datetime.now().strftime("%H%M")}',
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cache_cleared': request.args.get('cache', 'none')
        })
        
        # 明示的なCORSヘッダー追加
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        
        return response
        
    except Exception as e:
        print(f"[ERROR] Exception in extract: {str(e)}")
        import traceback
        traceback.print_exc()
        error_response = jsonify({
            'success': False, 
            'error': f'処理中にエラーが発生しました: {str(e)}',
            'debug_info': f'エラー詳細: {type(e).__name__}'
        })
        
        # エラーレスポンスにもCORSヘッダー追加
        error_response.headers.add('Access-Control-Allow-Origin', '*')
        error_response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        error_response.headers.add('Access-Control-Allow-Methods', 'POST')
        
        return error_response

@app.route('/api/access-info')
def access_info():
    return jsonify({
        'localURL': 'http://127.0.0.1:8087',
        'networkURL': 'http://localhost:8087',
        'ngrokURL': 'Not available'
    })

@app.route('/qr-code')
def qr_code():
    return jsonify({
        'success': True,
        'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    })

def open_browser():
    """
    サーバー起動後にブラウザを自動で開く
    """
    time.sleep(2)  # サーバー起動を待つ
    try:
        webbrowser.open('http://127.0.0.1:8087')
        print("[INFO] Browser opened automatically")
    except Exception as e:
        print(f"[WARN] Could not open browser automatically: {e}")

if __name__ == '__main__':
    from datetime import datetime
    current_time = datetime.now().strftime('%H:%M:%S')
    
    print("=" * 75)
    print("YouTube Transcript App - PRODUCTION v1.3.11")
    print("=" * 75)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Server URL: http://127.0.0.1:8087")
    print("Network URL: http://localhost:8087")
    print("=" * 75)
    print("Features:")
    print("   * YouTube API: ACTIVE (fetch method)")
    print("   * Text Formatting: ENHANCED")
    print("   * AI Summarization: Gemini 1.5 Flash")
    print("   * Design: v1.3.11-gradient-red")
    print("   * Version Auto-Update: ENABLED")
    print("   * Cache Detection: ACTIVE")
    print("   * Auto Browser: ENABLED")
    print("=" * 75)
    print("Server Status: READY")
    print("Tip: Browser will open automatically")
    print("=" * 75)
    
    # ブラウザ自動起動用のスレッド
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # サーバー起動（別ポートでテスト）
    app.run(host='127.0.0.1', port=8087, debug=False, threaded=True)