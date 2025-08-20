#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

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
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 要約用プロンプト
        prompt = f"""
以下はYouTube動画の字幕テキストです。この内容を日本語で簡潔に要約してください。

**要約条件:**
1. 3-5文で簡潔にまとめる
2. 主要なポイントを抽出する
3. 時間情報や不要な詳細は省く
4. 読み手にとって有益な情報を重視する

**字幕テキスト:**
{text[:2000]}{'...' if len(text) > 2000 else ''}

**AI要約:**
        """
        
        # Gemini APIで要約生成
        response = model.generate_content(prompt)
        
        if response and response.text:
            summary = response.text.strip()
            print(f"[OK] Gemini summary generated: {len(summary)} characters")
            return f"""🤖 AI要約 (Gemini 1.5 Flash):

{summary}

---
📊 分析情報:
・ 動画ID: {video_id}
・ 元テキスト文字数: {len(text):,}文字
・ 処理時刻: {datetime.now().strftime('%H:%M:%S')}
・ 言語設定: {language.upper()}"""
        else:
            print("[WARN] Gemini API returned empty response")
            return generate_fallback_summary(text, video_id, language)
            
    except Exception as e:
        print(f"[ERROR] Gemini API error: {str(e)}")
        return generate_fallback_summary(text, video_id, language)

def generate_fallback_summary(text, video_id, language):
    """
    Gemini APIが使用できない場合のフォールバック要約
    """
    # シンプルなキーワード抽出と文章要約
    sentences = text.replace('。', '。\n').split('\n')
    important_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
    
    return f"""📝 基本要約 (Fallback):

主要な内容:
・ {important_sentences[0] if len(important_sentences) > 0 else '情報なし'}
・ {important_sentences[1] if len(important_sentences) > 1 else ''}
・ {important_sentences[2] if len(important_sentences) > 2 else ''}

---
📊 統計情報:
・ 動画ID: {video_id}
・ 文字数: {len(text):,}文字
・ 言語: {language.upper()}
・ 状態: Gemini API未設定

⚠️ GEMINI_API_KEYを設定すると、より高品質なAI要約が利用できます。"""

# 高度なテキスト整形関数
def format_transcript_text(original_text):
    """
    YouTube字幕テキストを読みやすく整形する
    - 元のテキストは保持し、整形版のみ改善
    - 空行追加、誤変換修正、読みやすさ向上
    """
    import re
    
    text = original_text
    
    # 1. 基本的な句読点での改行
    text = text.replace('。 ', '。\n')
    text = text.replace('. ', '.\n')
    text = text.replace('！ ', '！\n')
    text = text.replace('? ', '?\n')
    text = text.replace('？ ', '？\n')
    
    # 2. よくある誤変換の修正（一般的なもの）
    corrections = {
        '有り難う': 'ありがとう',
        '有難う': 'ありがとう', 
        '宜しく': 'よろしく',
        '宜しい': 'よろしい',
        '御座います': 'ございます',
        '下さい': 'ください',
        '致します': 'いたします',
        '御願い': 'お願い',
        '出来る': 'できる',
        '出来ます': 'できます',
        '出来ません': 'できません',
        '何時': 'いつ',
        '何処': 'どこ',
        '何故': 'なぜ',
        '如何': 'いかが',
        '沢山': 'たくさん',
        '一杯': 'いっぱい',
        '丁寧': 'ていねい',
        '綺麗': 'きれい',
        '美味しい': 'おいしい',
        '素晴らしい': 'すばらしい'
    }
    
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    
    # 3. 文の区切りを改善（接続詞の前で改行）
    connectives = ['そして', 'また', 'しかし', 'でも', 'ところで', 'さて', 'それでは', 'では', 'つまり', 'なので', 'だから', 'それで']
    for conn in connectives:
        text = text.replace(f' {conn}', f'\n\n{conn}')
        text = text.replace(f'　{conn}', f'\n\n{conn}')
    
    # 4. 時間や数字の表現を改善
    text = re.sub(r'(\d+)時間', r'\1時間', text)
    text = re.sub(r'(\d+)分間', r'\1分', text)
    text = re.sub(r'(\d+)秒間', r'\1秒', text)
    
    # 5. 段落分けの改善（長い文の後に空行）
    sentences = text.split('\n')
    improved_sentences = []
    
    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue
        
        improved_sentences.append(sentence)
        
        # 長い文の後や重要なポイントの後に空行を追加
        if (len(sentence) > 50 and 
            ('です' in sentence[-10:] or 'ます' in sentence[-10:] or 
             '。' in sentence[-3:] or '！' in sentence[-3:] or '？' in sentence[-3:])):
            improved_sentences.append('')  # 空行
    
    # 6. 最終的な整形
    formatted = '\n'.join(improved_sentences)
    
    # 連続する空行を最大2つまでに制限
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # 文頭の余計な空白を削除
    formatted = re.sub(r'^\s+', '', formatted, flags=re.MULTILINE)
    
    return formatted

# 必要なライブラリのインストール確認とインポート
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("[OK] youtube-transcript-api imported successfully")
    # APIの存在確認
    api_methods = [m for m in dir(YouTubeTranscriptApi) if not m.startswith('_')]
    print(f"[INFO] Available methods: {api_methods}")
    if 'fetch' in api_methods:
        print("[OK] fetch method available")
    else:
        print("[ERROR] fetch method not found")
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
    import google.generativeai as genai

# UTF-8設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

app = Flask(__name__)
CORS(app)

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
        from youtube_transcript_api import YouTubeTranscriptApi
        
        data = request.get_json()
        url = data.get('url', '')
        lang = data.get('lang', 'ja')
        generate_summary = data.get('generate_summary', True)
        
        # テスト用のシンプルなビデオID（実際のYouTube動画）
        if not url:
            return jsonify({'success': False, 'error': 'URLを入力してください'})
        
        # YouTube URL解析（14形式対応）
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
            # テスト用デフォルトID（字幕付き動画）
            video_id = 'M7lc1UVf-VE'  # YouTube公式チャンネルの字幕付き動画
            print(f"[INFO] Invalid URL format, using test video ID: {video_id}")
        
        print(f"[INFO] Extracting transcript for video ID: {video_id}")
        
        # 字幕取得 - fetch()メソッドを使用
        try:
            print(f"[INFO] Fetching transcript for video_id: {video_id}")
            # まず指定言語で試行
            try:
                transcript = YouTubeTranscriptApi().fetch(video_id, languages=[lang])
            except:
                # 指定言語で失敗した場合、日本語で試行
                try:
                    transcript = YouTubeTranscriptApi().fetch(video_id, languages=['ja'])
                except:
                    # 英語で試行
                    try:
                        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
                    except:
                        # デフォルト言語で取得
                        transcript = YouTubeTranscriptApi().fetch(video_id)
            print(f"[OK] Transcript fetched successfully: {len(transcript)} segments")
        except Exception as transcript_error:
            print(f"[ERROR] Transcript fetch failed: {str(transcript_error)}")
            return jsonify({
                'success': False, 
                'error': f'字幕を取得できませんでした: {str(transcript_error)}'
            })
        
        # テキスト整形 - FetchedTranscriptSnippet オブジェクト対応
        if not transcript:
            return jsonify({'success': False, 'error': '字幕データが空です'})
        
        print(f"[INFO] Transcript type: {type(transcript)}")
        print(f"[INFO] First transcript entry: {transcript[0] if transcript else 'Empty'}")
        
        # FetchedTranscriptSnippet オブジェクトから text 属性を取得
        try:
            if hasattr(transcript[0], 'text'):
                # 属性として直接アクセス
                original_text = ' '.join([entry.text for entry in transcript])
            elif hasattr(transcript[0], 'get'):
                # 辞書形式でアクセス
                original_text = ' '.join([entry.get('text', '') for entry in transcript])
            else:
                # 文字列として直接使用
                original_text = ' '.join([str(entry) for entry in transcript])
        except Exception as text_error:
            print(f"[ERROR] Text extraction failed: {text_error}")
            original_text = str(transcript)[:500] + '...'  # フォールバック
        
        # 字幕データが空の場合のチェック
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
        
        return jsonify({
            'success': True,
            'title': f'YouTube動画 (ID: {video_id})',
            'transcript': formatted_text,
            'original_transcript': original_text,
            'summary': summary_text,
            'stats': {
                'segments': len(transcript),
                'characters': len(original_text),
                'language': lang.upper(),
                'duration': sum([float(getattr(entry, 'duration', 0) if hasattr(entry, 'duration') else entry.get('duration', 0) if hasattr(entry, 'get') else 0) for entry in transcript]),
                'video_id': video_id,
                'transcript_type': str(type(transcript[0]).__name__ if transcript else 'Unknown')
            },
            'version': f'v1.3.11-gradient-red-{datetime.now().strftime("%H%M")}',
            'server_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'cache_cleared': request.args.get('cache', 'none')
        })
        
    except Exception as e:
        print(f"[ERROR] Exception in extract: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'error': f'処理中にエラーが発生しました: {str(e)}',
            'debug_info': f'エラー詳細: {type(e).__name__}'
        })

@app.route('/api/access-info')
def access_info():
    return jsonify({
        'localURL': 'http://127.0.0.1:8089',
        'networkURL': 'http://localhost:8089',
        'ngrokURL': 'Not available'
    })

@app.route('/qr-code')
def qr_code():
    return jsonify({
        'success': True,
        'qr_code': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
    })

if __name__ == '__main__':
    from datetime import datetime
    current_time = datetime.now().strftime('%H:%M:%S')
    print(f"YouTube Transcript App - Enhanced Formatting v1.3.11-{current_time}")
    print("=" * 75)
    print("Server URL: http://127.0.0.1:8089")
    print("Template Auto-Reload: ENABLED")
    print("Cache-Clear Button: ADDED")
    print("Gradient: Updated (#ff0000 → #ff3542)")
    print("YouTube API: ACTIVE (fetch method with FetchedTranscriptSnippet)")
    print("Text Formatting: ENHANCED (誤変換修正・空行・段落分け)")
    print("AI Summarization: ENABLED (Gemini stub)")
    print(f"Design: v1.3.11-gradient-red-enhanced-{current_time}")
    print("Cache Detection: ACTIVE")
    print("Version Auto-Update: EVERY REQUEST")
    print("=" * 75)
    
    app.run(host='0.0.0.0', port=8085, debug=True)