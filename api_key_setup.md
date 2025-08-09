# YouTube Data API キー取得と設定ガイド

## YouTube Data API v3キーの取得方法

### 1. Google Cloud Console でプロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. プロジェクト名: `youtube-transcript-app`

### 2. YouTube Data API v3 を有効化

1. APIとサービス > ライブラリ に移動
2. "YouTube Data API v3" を検索
3. APIを有効にする

### 3. 認証情報（APIキー）を作成

1. APIとサービス > 認証情報 に移動
2. 「認証情報を作成」> 「APIキー」を選択
3. 作成されたAPIキーをコピー
4. 「キーを制限」をクリック（推奨）
   - アプリケーションの制限: 「なし」または「IPアドレス」
   - API制限: 「YouTube Data API v3」のみに制限

### 4. 環境変数への設定

#### Windows (開発環境)
```cmd
setx YOUTUBE_API_KEY "YOUR_API_KEY_HERE"
```

#### .envファイル (推奨)
```bash
# .env file
YOUTUBE_API_KEY=YOUR_API_KEY_HERE
```

#### Cloud Run環境
```bash
# デプロイ時に指定
gcloud run deploy --set-env-vars="YOUTUBE_API_KEY=YOUR_API_KEY_HERE"
```

## APIキーのテスト

### 簡単な動作確認
```bash
curl "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key=YOUR_API_KEY"
```

正常なレスポンス例:
```json
{
  "items": [
    {
      "snippet": {
        "title": "Rick Astley - Never Gonna Give You Up (Video)"
      }
    }
  ]
}
```

## 使用制限

### クォータ制限
- 1日あたり10,000リクエスト（無料枠）
- 1リクエスト = 1-3単位消費

### コスト
- 無料枠: 1日10,000単位
- 超過料金: $0.25 per 10,000 units

### セキュリティ

1. **APIキーの保護**
   - 環境変数またはSecret Manager使用
   - コードにハードコード禁止
   - .gitignoreに.envを追加

2. **IP制限**（本番環境推奨）
   - 特定のIPからのみアクセス許可

3. **リファラー制限**（Web環境）
   - 特定のドメインからのみアクセス許可

## トラブルシューティング

### よくあるエラー

#### 403 Forbidden
- APIが有効になっていない
- APIキーが無効
- クォータ制限に達している

#### 400 Bad Request
- リクエストパラメータが不正
- 動画IDが存在しない

### デバッグ用テストURL

YouTube動画ID: `dQw4w9WgXcQ` (Rick Roll - テスト用に最適)

```bash
# テスト用コマンド
curl "https://www.googleapis.com/youtube/v3/videos?part=snippet&id=dQw4w9WgXcQ&key=YOUR_API_KEY"
```

## 本番環境での推奨設定

### Google Cloud Secret Manager
```bash
# シークレット作成
gcloud secrets create youtube-api-key --data-file=- <<< "YOUR_API_KEY"

# Cloud Runからアクセス
gcloud run deploy --set-secrets="YOUTUBE_API_KEY=youtube-api-key:latest"
```

### 監視設定
- Cloud MonitoringでAPI使用量を監視
- アラート設定でクォータ制限前に通知

## まとめ

1. Google Cloud Consoleでプロジェクト作成
2. YouTube Data API v3を有効化
3. APIキーを作成・制限設定
4. 環境変数またはSecret Managerに保存
5. テスト実行で動作確認

**重要**: APIキーは機密情報として適切に管理してください。