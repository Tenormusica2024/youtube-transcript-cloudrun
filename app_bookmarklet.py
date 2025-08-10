"""
YouTube Transcript Extractor - Bookmarklet + Cloud Run版
セキュリティ強化＋要約特化アーキテクチャ
"""

import os
import re
import json
import logging
import time
from datetime import datetime
from collections import Counter
from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask アプリケーション設定
app = Flask(__name__, static_folder='.', static_url_path='')

# CORS設定（YouTube.comからのリクエストを許可）
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://www.youtube.com",
            "https://youtube.com", 
            "https://music.youtube.com",
            "https://m.youtube.com",
            # 開発環境用
            "http://localhost:*",
            "http://127.0.0.1:*"
        ],
        "methods": ["POST", "GET", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 環境変数読み込み
load_dotenv()

# Cloud Run用ポート設定
PORT = int(os.environ.get('PORT', 8080))

# --- セキュリティ強化された簡易要約システム ---
class SecureNaiveSummarizer:
    """セキュリティ強化された軽量要約システム"""
    
    def __init__(self):
        self.max_length = int(os.environ.get('MAX_TRANSCRIPT_LENGTH', 50000))
        self.max_sentences = int(os.environ.get('SUMMARY_SENTENCES', 4))
        self.rate_limit = {}  # 簡易レート制限
        
    def is_rate_limited(self, client_ip):
        """簡易レート制限チェック"""
        now = time.time()
        if client_ip not in self.rate_limit:
            self.rate_limit[client_ip] = []
        
        # 過去10分間のリクエストをカウント
        recent_requests = [t for t in self.rate_limit[client_ip] if now - t < 600]
        self.rate_limit[client_ip] = recent_requests
        
        max_requests = int(os.environ.get('RATE_LIMIT_PER_10MIN', 20))
        return len(recent_requests) >= max_requests
    
    def record_request(self, client_ip):
        """リクエストを記録"""
        if client_ip not in self.rate_limit:
            self.rate_limit[client_ip] = []
        self.rate_limit[client_ip].append(time.time())
    
    def sanitize_text(self, text):
        """テキストのサニタイズ"""
        if not text or not isinstance(text, str):
            return ""
        
        # 長さ制限
        if len(text) > self.max_length:
            text = text[:self.max_length] + "...(truncated)"
        
        # 危険な文字を除去
        text = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', text)
        
        return text.strip()
    
    def extract_keywords(self, text, max_keywords=10):
        """キーワード抽出"""
        # 日本語・英語の単語を抽出
        words = re.findall(r'[\w\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]{2,}', text.lower())
        
        # ストップワードを除去（簡易版）
        stopwords = {
            'の', 'は', 'を', 'に', 'が', 'で', 'と', 'て', 'だ', 'である', 'です', 'ます',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
        words = [w for w in words if w not in stopwords and len(w) > 1]
        
        # 頻出語をカウント
        counter = Counter(words)
        return [word for word, count in counter.most_common(max_keywords)]
    
    def summarize(self, text):
        """テキスト要約の実行"""
        text = self.sanitize_text(text)
        if not text:
            return "", {"error": "Empty or invalid text"}
        
        # 文章を分割
        sentences = re.split(r'(?<=[。.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return "", {"error": "No sentences found"}
        
        # 要約作成（先頭の重要な文を選択）
        summary_sentences = sentences[:self.max_sentences]
        summary = '\n'.join(summary_sentences)
        
        # キーワード抽出
        keywords = self.extract_keywords(text)
        
        # 統計情報
        stats = {
            "original_length": len(text),
            "summary_length": len(summary),
            "total_sentences": len(sentences),
            "summary_sentences": len(summary_sentences),
            "keywords": keywords[:5],  # 上位5個のキーワード
            "processed_at": datetime.now().isoformat(),
            "mode": "secure_naive"
        }
        
        return summary, stats

# グローバル要約器インスタンス
summarizer = SecureNaiveSummarizer()

# --- AI要約機能（オプション：Gemini） ---
def get_gemini_summary(transcript):
    """Gemini APIを使用した高度な要約（オプション）"""
    try:
        from google import genai
        
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            logger.info("Gemini API key not found, using naive summarizer")
            return None
        
        # Gemini API設定
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        以下のYouTube動画の字幕を要約してください：

        【要約の要件】
        - 3-4文程度の簡潔な要約
        - 主要なポイントを箇条書きで2-3個
        - 専門用語がある場合は簡単に説明

        【字幕テキスト】
        {transcript[:8000]}  # APIの制限を考慮
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return None

# --- ルーティング ---

@app.route('/')
def index():
    """ランディングページ"""
    try:
        return send_from_directory('.', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {e}")
        return """
        <h1>YouTube Transcript Extractor</h1>
        <p>ランディングページが見つかりません。index.htmlファイルを確認してください。</p>
        <p><a href="/healthz">ヘルスチェック</a></p>
        """, 404

@app.route('/api/summarize', methods=['POST', 'OPTIONS'])
def api_summarize():
    """メイン要約API - ブックマークレットから呼び出される"""
    
    # CORS preflight対応
    if request.method == 'OPTIONS':
        return '', 200
    
    # レート制限チェック
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if summarizer.is_rate_limited(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return jsonify({
            "error": "Rate limit exceeded", 
            "message": "10分間に20回までの制限があります"
        }), 429
    
    try:
        # リクエスト データ取得
        data = request.get_json(force=True)
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        video_id = data.get('videoId', '')
        transcript = data.get('transcript', '')
        
        if not transcript:
            return jsonify({"error": "Transcript is required"}), 400
        
        logger.info(f"Processing summarization request for video: {video_id[:20]}...")
        
        # リクエストを記録（レート制限用）
        summarizer.record_request(client_ip)
        
        # AI要約を試行（利用可能な場合）
        ai_summary = get_gemini_summary(transcript)
        
        if ai_summary:
            # AI要約成功
            summary = ai_summary
            stats = {
                "mode": "gemini_ai",
                "original_length": len(transcript),
                "summary_length": len(summary),
                "processed_at": datetime.now().isoformat(),
                "ai_powered": True
            }
        else:
            # フォールバック：簡易要約
            summary, stats = summarizer.summarize(transcript)
        
        # レスポンス構築
        response_data = {
            "success": True,
            "videoId": video_id,
            "summary": summary,
            "meta": {
                "tokens": f"処理完了 - 文字数: {stats.get('original_length', 0)} → {stats.get('summary_length', 0)}",
                **stats
            }
        }
        
        logger.info(f"Successfully processed video {video_id} with {stats.get('mode', 'unknown')} mode")
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in summarize API: {e}")
        return jsonify({
            "success": False,
            "error": "Internal server error",
            "message": "要約処理中にエラーが発生しました"
        }), 500

@app.route('/healthz')
def healthz():
    """ヘルスチェック"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "bookmarklet-v1.0",
        "features": {
            "gemini_ai": bool(os.environ.get('GEMINI_API_KEY')),
            "cors_enabled": True,
            "rate_limiting": True
        }
    }

@app.route('/api/status')
def api_status():
    """API詳細ステータス"""
    active_ips = len(summarizer.rate_limit)
    total_requests = sum(len(reqs) for reqs in summarizer.rate_limit.values())
    
    return jsonify({
        "service": "YouTube Transcript Extractor",
        "architecture": "Bookmarklet + Cloud Run",
        "active_clients": active_ips,
        "total_requests_tracked": total_requests,
        "rate_limit": "20 requests per 10 minutes per IP",
        "ai_summary": bool(os.environ.get('GEMINI_API_KEY')),
        "uptime": "Running"
    })

# --- セキュリティヘッダー ---
@app.after_request
def add_security_headers(response):
    """セキュリティヘッダーの追加"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # CORS関連ヘッダーは flask-cors が自動追加
    return response

# --- エラーハンドラー ---
@app.errorhandler(404)
def not_found_error(error):
    """404エラーハンドラー"""
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": ["/", "/api/summarize", "/healthz", "/api/status"]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error",
        "message": "予期しないエラーが発生しました"
    }), 500

if __name__ == '__main__':
    # Cloud Run環境かローカル環境かを判定
    is_cloud_run = os.environ.get('K_SERVICE') is not None
    
    if is_cloud_run:
        logger.info(f"Starting Cloud Run server on port {PORT}")
        app.run(host='0.0.0.0', port=PORT, debug=False)
    else:
        # ローカル開発環境
        logger.info(f"Starting local development server on port {PORT}")
        logger.info("Available endpoints:")
        logger.info("  GET  / - Landing page")
        logger.info("  POST /api/summarize - Main API")
        logger.info("  GET  /healthz - Health check")
        logger.info("  GET  /api/status - API status")
        app.run(host='127.0.0.1', port=PORT, debug=True)