#!/usr/bin/env python3
"""
YouTube字幕抽出 - 簡単なローカルサーバー
"""

import base64
import io
import json
import logging
import os
import time
from datetime import datetime

import qrcode
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS

# 環境変数読み込み
load_dotenv()

# 環境変数デバッグ
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(
    f"GEMINI_API_KEY loaded: {'SET' if os.environ.get('GEMINI_API_KEY') else 'NOT SET'}"
)

import os

import google.generativeai as genai

# hybrid_transcript_toolから必要な関数をインポート
from hybrid_transcript_tool import (extract_video_id, format_transcript_text,
                                    get_transcript_local)

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask アプリケーション設定
app = Flask(__name__)
CORS(app)


def get_ngrok_url():
    """ngrok APIから現在のURLを動的取得"""
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=3)
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https" and "localhost:5001" in tunnel.get(
                    "config", {}
                ).get("addr", ""):
                    public_url = tunnel.get("public_url")
                    if public_url:
                        logger.info(f"ngrok URL取得成功: {public_url}")
                        return public_url
        logger.warning("ngrok URL取得失敗 - localhost使用")
        return "http://localhost:5001"
    except Exception as e:
        logger.warning(f"ngrok API接続失敗: {e}")
        return "http://localhost:5001"


def get_ai_api_key():
    """AI APIキーを取得"""
    # 環境変数から取得
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        logger.warning("AI API key not found - using basic formatting")
        return None

    logger.info("AI API key configured successfully")
    return api_key


def format_with_ai(text, api_key):
    """AIでテキストを整形"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-001")

        # より詳細で粒度の高い要約プロンプト
        prompt = f"""YouTube字幕の整形処理を実行してください。

以下の字幕テキストを読みやすく整形し、非常に詳細で包括的な要約を作成してください：

【字幕内容】
{text}

【整形要求】
・適切な段落分けを行う（2-3文ごとに改行）
・繰り返し表現や不自然な接続を修正
・読みやすい日本語文章にする
・必ず行間スペースを入れる（段落間は空行を挿入）

【要約要求 - 動画の長さに応じて最大限詳細に】
・動画の内容量に応じて、可能な限り詳細で包括的な要約を作成する
・短い動画でも重要な情報は漏らさず、長い動画では内容を削らずに全体を網羅する
・重要なポイントはすべて箇条書きにする（数に制限なし）
・細かい具体例、数値、固有名詞、専門用語、引用をすべて含める
・話の流れ、論理展開、根拠、因果関係を詳しく説明する
・背景情報、文脈、関連情報、前提条件も詳細に記述する
・発言者の意図、ニュアンス、感情表現、強調点も含める
・時系列やステップがある場合は順序立てて詳しく説明する
・見落としがちな細かい情報や補足事項も含める

【回答形式】
整形後テキスト：

[ここに段落分けされた読みやすいテキスト]

要約：

■ 動画の全体概要
[動画の目的、テーマ、対象者について詳しく説明（動画の長さに応じて適切な分量で）]

■ 導入部・背景情報
[動画の背景、きっかけ、前提条件について詳しく説明（該当する内容がある場合）]

■ 主要な内容・ポイント（網羅的詳細版）
[動画で言及されたすべての重要ポイントを漏らさず詳細に箇条書き]
• [ポイント1: 具体的な内容、数値、事例、引用を含めて詳しく説明]
• [ポイント2: 関連する背景情報、根拠、因果関係も含めて詳しく説明]
• [ポイント3: 具体的な手順、プロセス、ステップを順序立てて詳しく説明]
• [以降、動画の内容に応じて必要な分だけ詳細なポイントを追加]

■ 具体的な事例・実例・デモンストレーション
[動画で紹介された具体例、実演、デモ、比較、実験結果などを詳しく記述（該当する場合）]

■ 技術的詳細・専門情報・データ
[専門的な内容、技術仕様、数値データ、統計、研究結果などを詳しく説明（該当する場合）]

■ 注意点・制限事項・補足情報
[重要な注意事項、制限、リスク、追加の補足情報を詳しく記述（該当する場合）]

■ 引用・参考情報・関連リソース
[動画内で言及された参考文献、関連リンク、推奨リソースなど（該当する場合）]

■ 結論・まとめ・今後の展望
[動画の結論、重要なメッセージ、今後の方向性、発言者の最終的な主張を詳しく説明]

■ 視聴者への推奨事項・次のステップ
[視聴者が次に取るべき行動、推奨事項、実践方法など（該当する場合）]"""

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                max_output_tokens=15000,  # 詳細な要約のため大幅に増量
                top_p=0.8,
            ),
        )

        return response.text
    except Exception as e:
        logger.error(f"AI整形エラー: {e}")
        return text


def generate_qr_code(url):
    """QRコード生成"""
    try:
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)

        # Base64エンコード
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return None


# HTML テンプレート
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Transcript Extractor</title>
    <style>
        @keyframes waterReflection {
            0% {
                background-position: 0% 50%;
                transform: translateX(-100px);
                opacity: 0.075;
            }
            50% {
                opacity: 0.175;
            }
            100% {
                background-position: 100% 50%;
                transform: translateX(100px);
                opacity: 0.075;
            }
        }
        
        @keyframes shimmer {
            0% {
                transform: translateX(-100%);
            }
            100% {
                transform: translateX(100%);
            }
        }
        
        @keyframes ripple {
            0% {
                box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.1);
            }
            70% {
                box-shadow: 0 0 0 20px rgba(255, 255, 255, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
            }
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(255, 255, 255, 0.025) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.025) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 255, 255, 0.0125) 0%, transparent 50%);
            /* animation: waterReflection 60s ease-in-out infinite; */
            pointer-events: none;
            z-index: 1;
        }
        
        body::after {
            content: '';
            position: fixed;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.025),
                transparent
            );
            /* animation: shimmer 30s ease-in-out infinite; */
            pointer-events: none;
            z-index: 1;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 0;
            border-radius: 20px;
            box-shadow: 
                0 10px 30px rgba(0,0,0,0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            overflow: hidden;
            position: relative;
            z-index: 2;
        }
        
        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 2px;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            /* animation: shimmer 20s ease-in-out infinite; */
        }
        .header {
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.0375) 0%, transparent 50%),
                radial-gradient(circle at 70% 80%, rgba(255, 255, 255, 0.025) 0%, transparent 50%);
            /* animation: waterReflection 40s ease-in-out infinite; */
            pointer-events: none;
        }
        
        .header::after {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 50%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.05),
                transparent
            );
            /* animation: shimmer 40s ease-in-out infinite; */
            pointer-events: none;
        }
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=SF+Pro+Display:wght@300;400;500;600;700&display=swap');
        
        @keyframes platinumShine {
            0% {
                background-position: -200% 0;
            }
            100% {
                background-position: 200% 0;
            }
        }
        
        h1 {
            margin: 0;
            font-size: 32px;
            font-weight: 500;
            font-family: 'SF Pro Display', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            position: relative;
            z-index: 1;
            background: linear-gradient(135deg, 
                #ffffff 0%, 
                #f8f9fa 10%,
                #e9ecef 25%, 
                #dee2e6 35%,
                #ced4da 50%, 
                #adb5bd 65%,
                #868e96 75%,
                #6c757d 85%,
                #495057 95%,
                #343a40 100%);
            background-size: 400% 100%;
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: 1px;
            line-height: 1.2;
            text-align: center;
            filter: drop-shadow(0 2px 4px rgba(255, 255, 255, 0.3));
        }
        
        h1::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(45deg, 
                transparent 30%, 
                rgba(255, 255, 255, 0.075) 50%, 
                transparent 70%);
            background-size: 200% 200%;
            /* animation: platinumShine 20s ease-in-out infinite reverse; */
            border-radius: 4px;
            z-index: -1;
        }
        .content {
            padding: 30px;
        }
        .form-section {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(5px);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 
                0 4px 15px rgba(0,0,0,0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        .form-section::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: 
                radial-gradient(circle, rgba(255, 255, 255, 0.0125) 0%, transparent 70%);
            /* animation: ripple 30s ease-in-out infinite; */
            pointer-events: none;
        }
        .form-group {
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }
        input[type="text"], select {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            box-sizing: border-box;
            transition: border-color 0.3s ease;
            background: rgba(255, 255, 255, 0.9);
            position: relative;
            z-index: 1;
        }
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #ff0000;
            box-shadow: 0 0 0 3px rgba(255, 0, 0, 0.1);
        }
        button {
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            transition: all 0.5s ease;
        }
        
        button:hover::before {
            left: 100%;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 0, 0, 0.4);
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        #result {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 25px;
            margin-top: 20px;
            box-shadow: 
                0 4px 15px rgba(0,0,0,0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.3);
            position: relative;
            overflow: hidden;
        }
        
        #result::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 10% 90%, rgba(255, 0, 0, 0.0125) 0%, transparent 50%),
                radial-gradient(circle at 90% 10%, rgba(255, 0, 0, 0.0075) 0%, transparent 50%);
            /* animation: waterReflection 80s ease-in-out infinite; */
            pointer-events: none;
        }
        .hidden {
            display: none;
        }
        .error {
            color: #ff0000;
            background-color: #ffe6e6;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ffcccc;
        }
        .success {
            color: #008000;
            background-color: #e6ffe6;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccffcc;
        }
        .loading {
            text-align: center;
            color: #666;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-family: monospace;
            resize: vertical;
        }
        #summaryText {
            height: 250px;
            background-color: #f0f8ff;
            font-size: 14px;
            line-height: 1.6;
        }
        .qr-section {
            margin-bottom: 30px;
            text-align: center;
            padding: 25px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(5px);
            border-radius: 15px;
            box-shadow: 
                0 4px 15px rgba(0,0,0,0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid #ff0000;
            position: relative;
            overflow: hidden;
        }
        
        .qr-section::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 0, 0, 0.0125),
                transparent
            );
            /* animation: shimmer 50s ease-in-out infinite; */
            pointer-events: none;
        }
        .qr-section h3 {
            margin: 0 0 20px 0;
            color: #ff0000;
            font-size: 18px;
            font-weight: 600;
        }
        .qr-code {
            margin: 10px 0;
        }
        .qr-url {
            font-family: monospace;
            color: #007bff;
            word-break: break-all;
            margin: 10px 0;
            padding: 10px;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 3px;
        }
        .refresh-btn {
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            padding: 10px 20px;
            font-size: 14px;
            margin: 10px;
            width: auto;
            display: inline-block;
            border-radius: 25px;
            box-shadow: 0 3px 10px rgba(255, 0, 0, 0.3);
        }
        .refresh-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.4);
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .container {
                margin: 0;
                border-radius: 15px;
            }
            
            .header {
                padding: 20px;
            }
            
            h1 {
                font-size: 22px;
            }
            
            .content {
                padding: 20px;
            }
            
            .form-section, .qr-section {
                padding: 20px;
                margin-bottom: 15px;
            }
            
            .form-group {
                margin-bottom: 15px;
            }
            
            input[type="text"], select {
                font-size: 16px;
                padding: 12px;
            }
            
            button {
                padding: 12px 24px;
                font-size: 16px;
            }
            
            .qr-code img {
                max-width: 150px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>YouTube要約アプリ</h1>
        </div>
        
        <div class="content">
        
        <!-- QRコード表示セクション -->
        <div class="qr-section">
            <h3>📱 スマホアクセス用QRコード</h3>
            <div id="qrCodeDisplay">
                <p>QRコードを生成中...</p>
            </div>
            <button type="button" class="refresh-btn" onclick="refreshQRCode()">QRコード更新</button>
        </div>
        
        <div class="form-section">
            <form id="extractForm">
                <div class="form-group">
                    <label for="url">YouTube URL:</label>
                    <input type="text" id="url" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
                </div>
                
                <div class="form-group">
                    <label for="lang">言語:</label>
                    <select id="lang" name="lang">
                        <option value="ja">日本語</option>
                        <option value="en">English</option>
                        <option value="ko">한국어</option>
                        <option value="zh">中文</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="format">出力フォーマット:</label>
                    <select id="format" name="format">
                        <option value="txt">テキスト</option>
                        <option value="json">JSON</option>
                        <option value="srt">SRT (字幕ファイル)</option>
                    </select>
                </div>
                
                <button type="submit" id="submitBtn">字幕を抽出</button>
            </form>
        </div>
        
        <div id="result" class="hidden">
            <h2>結果</h2>
            <div id="resultContent"></div>
        </div>
        
        </div> <!-- content end -->
    </div>

    <script>
        // QRコード生成・表示関数
        async function loadQRCode() {
            try {
                const response = await fetch('/qr-code');
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('qrCodeDisplay').innerHTML = `
                        <div class="qr-code">
                            <img src="${data.qr_code}" alt="QRコード" style="max-width: 200px;">
                        </div>
                        <div class="qr-url">
                            <strong>スマホアクセスURL:</strong><br>
                            ${data.url}
                        </div>
                        <p><small>📱 スマホでQRコードをスキャンしてアクセス</small></p>
                    `;
                } else {
                    document.getElementById('qrCodeDisplay').innerHTML = `
                        <p style="color: #ff0000;">QRコード生成失敗: ${data.error}</p>
                    `;
                }
            } catch (error) {
                document.getElementById('qrCodeDisplay').innerHTML = `
                    <p style="color: #ff0000;">エラー: ${error.message}</p>
                `;
            }
        }
        
        // QRコード更新関数
        function refreshQRCode() {
            document.getElementById('qrCodeDisplay').innerHTML = '<p>QRコードを更新中...</p>';
            loadQRCode();
        }
        
        // ページ読み込み時にQRコード生成
        window.addEventListener('load', loadQRCode);
        
        document.getElementById('extractForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const form = e.target;
            const submitBtn = document.getElementById('submitBtn');
            const result = document.getElementById('result');
            const resultContent = document.getElementById('resultContent');
            
            // ボタンを無効化
            submitBtn.disabled = true;
            submitBtn.textContent = '処理中...';
            
            // 結果エリアを表示
            result.classList.remove('hidden');
            resultContent.innerHTML = '<div class="loading">字幕を取得中...</div>';
            
            try {
                const formData = new FormData(form);
                const data = {
                    url: formData.get('url'),
                    lang: formData.get('lang'),
                    format: formData.get('format')
                };
                
                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer hybrid-yt-token-2024'
                    },
                    body: JSON.stringify(data)
                });
                
                const result_data = await response.json();
                
                if (result_data.success) {
                    const stats = result_data.stats || {};
                    resultContent.innerHTML = `
                        <div class="success">
                            <h3>[OK] 抽出成功</h3>
                            <p><strong>動画ID:</strong> ${result_data.video_id || 'Unknown'}</p>
                            <p><strong>文字数:</strong> ${stats.characters || stats.total_characters || 'Unknown'}</p>
                            <p><strong>セグメント数:</strong> ${stats.segments || 'Unknown'}</p>
                            <p><strong>言語:</strong> ${stats.language || 'Unknown'}</p>
                        </div>
                        <h4>字幕テキスト（AI整形済み）:</h4>
                        <textarea id="transcriptText" readonly>${result_data.formatted_transcript || result_data.transcript}</textarea>
                        
                        <h4 style="margin-top: 20px;">詳細な要約:</h4>
                        <textarea id="summaryText" readonly>${result_data.summary || '要約を生成中...'}</textarea>
                    `;
                } else {
                    resultContent.innerHTML = `
                        <div class="error">
                            <h3>[ERROR] エラー</h3>
                            <p>${result_data.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultContent.innerHTML = `
                    <div class="error">
                        <h3>[ERROR] 通信エラー</h3>
                        <p>サーバーとの通信でエラーが発生しました: ${error.message}</p>
                    </div>
                `;
            } finally {
                // ボタンを再有効化
                submitBtn.disabled = false;
                submitBtn.textContent = '字幕を抽出';
            }
        });
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """メインページ"""
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    """ヘルスチェックエンドポイント"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "YouTube Transcript Extractor - Local",
        }
    )


@app.route("/extract", methods=["POST"])
def extract():
    """字幕抽出エンドポイント"""
    try:
        logger.info("Extract endpoint called")
        data = request.json
        logger.info(f"Request data: {data}")

        url = data.get("url")
        lang = data.get("lang", "auto")

        if not url:
            return jsonify({"success": False, "error": "URLが指定されていません"}), 400

        logger.info(f"Processing URL: {url}, Lang: {lang}")

        # 動画ID取得
        video_id = extract_video_id(url)
        if not video_id:
            return (
                jsonify({"success": False, "error": "有効なYouTube URLではありません"}),
                400,
            )

        logger.info(f"Processing video: {video_id}")

        # 字幕取得
        transcript, detected_lang = get_transcript_local(video_id, lang)

        if not transcript:
            return jsonify({"success": False, "error": "字幕の取得に失敗しました"}), 400

        # プレーンテキストに変換
        transcript_text = format_transcript_text(transcript)

        # AI整形と要約を実行
        formatted_transcript = transcript_text
        summary_text = ""

        try:
            api_key = get_ai_api_key()
            if api_key:
                logger.info("AI整形・要約を実行中...")
                ai_response = format_with_ai(transcript_text, api_key)
                logger.info("AI処理完了")

                # 要約と整形テキストを分離
                if "要約：" in ai_response:
                    parts = ai_response.split("要約：", 1)
                    if len(parts) > 1:
                        summary_text = parts[1].strip()
                        formatted_transcript = (
                            parts[0].replace("整形後テキスト：", "").strip()
                        )
                elif "【要約】" in ai_response:
                    parts = ai_response.split("【要約】", 1)
                    if len(parts) > 1:
                        summary_text = parts[1].strip()
                        formatted_transcript = (
                            parts[0].replace("整形後テキスト：", "").strip()
                        )
                else:
                    formatted_transcript = ai_response
                    summary_text = "AI要約の分離に失敗しました"

                # 不要な接頭辞を削除
                formatted_transcript = formatted_transcript.replace(
                    "整形後テキスト：", ""
                )
                formatted_transcript = formatted_transcript.replace(
                    "**整形後テキスト：**", ""
                )
                formatted_transcript = formatted_transcript.strip()

            else:
                logger.warning("GEMINI_API_KEY未設定 - 基本整形を使用")
                summary_text = "AI要約機能を使用するにはGEMINI_API_KEYが必要です。"

        except Exception as e:
            logger.error(f"AI処理エラー: {e}")
            summary_text = "AI処理中にエラーが発生しました。"

        # 統計情報
        stats = {
            "segments": len(transcript),
            "characters": len(formatted_transcript),
            "language": detected_lang,
        }

        response_data = {
            "success": True,
            "video_id": video_id,
            "transcript": formatted_transcript,
            "formatted_transcript": formatted_transcript,
            "summary": summary_text,
            "stats": stats,
        }

        logger.info(f"Successfully processed video {video_id}")
        return jsonify(response_data)

    except ValueError as e:
        logger.warning(f"User error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in extract endpoint: {e}")
        return (
            jsonify(
                {"success": False, "error": f"予期しないエラーが発生しました: {str(e)}"}
            ),
            500,
        )


@app.route("/qr-code")
def generate_qr():
    """QRコード生成エンドポイント"""
    try:
        logger.info("QRコード生成リクエスト受信")

        # ngrok URLを動的取得
        ngrok_url = get_ngrok_url()
        logger.info(f"使用URL: {ngrok_url}")

        # QRコード生成
        qr_code_data = generate_qr_code(ngrok_url)

        if qr_code_data:
            return jsonify({"success": True, "qr_code": qr_code_data, "url": ngrok_url})
        else:
            return (
                jsonify({"success": False, "error": "QRコード生成に失敗しました"}),
                500,
            )

    except Exception as e:
        logger.error(f"QRコード生成エラー: {e}")
        return (
            jsonify({"success": False, "error": f"QRコード生成エラー: {str(e)}"}),
            500,
        )


if __name__ == "__main__":
    port = 5001
    logger.info(f"Starting simple YouTube transcript server on port {port}")
    logger.info(f"Open your browser to: http://localhost:{port}")

    try:
        app.run(host="127.0.0.1", port=port, debug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        print(f"Error: {e}")
        print("Try using a different port or check if the port is already in use.")
