# AI FM Podcast バックアップ情報

## バックアップ作成日時
- **作成日時**: 2025年9月9日 07:46:17
- **バックアップ元**: `C:\Users\Tenormusica\ai-fm-podcast-backup-v3.6.1-deploy`
- **バックアップ先**: `C:\Users\Tenormusica\ai-fm-podcast-backup-v3.6.1-deploy-20250909-074617`

## バックアップ時点のプロジェクト状態

### デプロイ状況
- **Cloud Run URL**: https://ai-fm-podcast-spacing-final-ycqe3vmjva-uc.a.run.app
- **最新リビジョン**: ai-fm-podcast-spacing-final-00017-7mb
- **プロジェクトID**: yt-transcript-demo-2025
- **リージョン**: us-central1

### 実装済み機能・修正
1. ✅ MP3アートワークblobURLエラー修正
2. ✅ Webブラウザ版サイドバートグルボタン削除
3. ✅ モバイル版アップロード画面レイアウト修正
4. ✅ モバイル版タイトル表示問題の調査・修正・元に戻し

### 主要ファイル
- **app.py** (143KB) - メインFlaskアプリケーション
- **templates/index.html** - フロントエンドテンプレート
- **static/css/style-20250906-menu-fix.css** - メインCSS
- **static/js/firebase-config.js** - Firebase設定・認証
- **Dockerfile** - コンテナビルド設定
- **cloudbuild.yaml** - Cloud Build設定

### 技術スタック
- **Backend**: Python Flask
- **Frontend**: HTML/CSS/JavaScript
- **Authentication**: Firebase Auth
- **Database**: Cloud Firestore
- **Storage**: Google Cloud Storage
- **Deployment**: Google Cloud Run

## バックアップファイル構造
```
ai-fm-podcast-backup-v3.6.1-deploy-20250909-074617/
├── app.py
├── Dockerfile
├── requirements.txt
├── cloudbuild.yaml
├── templates/
│   └── index.html
├── static/
│   ├── css/
│   └── js/
└── [各種レポートファイル]
```

## 注意事項
- このバックアップは完全な機能バージョンです
- モバイル版タイトル表示は中央配置（padding修正を元に戻した状態）
- Firebase認証が正常に動作することを確認済み
- Cloud Runでのデプロイが正常に完了した状態