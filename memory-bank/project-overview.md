# YouTube Transcript WebApp with Gemini AI

## プロジェクト概要
YouTube動画の字幕を自動抽出し、Gemini AIで整形・要約するWebアプリケーション

## 主要機能
1. **YouTube字幕抽出**: YouTube Data API v3を使用
2. **AI自動整形**: 句点後に空行を挿入して読みやすく整形
3. **AI自動要約**: 500-800文字の詳細な要約を生成
4. **多言語対応**: 日本語、英語、韓国語、中国語

## 技術スタック
- **Backend**: Flask (Python 3.10)
- **AI**: Google Gemini 2.0 Flash
- **APIs**: YouTube Data API v3, YouTube Transcript API
- **Deployment**: Google Cloud Run
- **Container**: Docker

## ディレクトリ構造
```
youtube_transcript_webapp/
├── app.py                 # メインアプリケーション
├── templates/
│   └── index.html        # フロントエンドUI
├── static/
│   └── style.css         # スタイルシート
├── requirements.txt       # Python依存関係
├── Dockerfile            # コンテナ設定
├── cloudbuild.yaml       # Cloud Build設定
└── .env                  # 環境変数（APIキー）
```

## APIキー設定
- YOUTUBE_API_KEY: YouTube Data API v3用
- GEMINI_API_KEY: Gemini AI用

## デプロイ情報
- **サービス名**: youtube-transcript-webapp
- **リージョン**: asia-northeast1
- **メモリ**: 512Mi
- **タイムアウト**: 300秒
- **最大インスタンス**: 10