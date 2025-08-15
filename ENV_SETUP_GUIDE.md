# YouTube Transcript Extractor - 環境変数設定ガイド

## 📋 必須環境変数一覧

このアプリケーションを正常に動作させるためには、以下の環境変数を設定する必要があります。

### 🔑 APIキー類

| 変数名 | 必須 | 説明 | 取得方法 | 例 |
|--------|------|------|----------|-----|
| `YOUTUBE_API_KEY` | ✅ | YouTube Data API v3のAPIキー | [Google Cloud Console](https://console.cloud.google.com/) | `AIzaSyABCDEF...` (39文字) |
| `GEMINI_API_KEY` | ✅ | Google Gemini AIのAPIキー | [Google AI Studio](https://makersuite.google.com/app/apikey) | `AIzaSyABCDEF...` (39文字) |
| `TRANSCRIPT_API_TOKEN` | ✅ | `/extract`エンドポイント認証用トークン | カスタム設定 | `hybrid-yt-token-2024` |

### ⚙️ 設定値

| 変数名 | 必須 | デフォルト値 | 説明 | 有効な値 |
|--------|------|-------------|------|----------|
| `PORT` | ❌ | `8765` | サーバーポート番号 | `1024-65535` |
| `MAX_TRANSCRIPT_LENGTH` | ❌ | `50000` | 字幕最大文字数制限 | `1000+` |
| `PYTHONIOENCODING` | ❌ | `utf-8` | Python文字エンコーディング | `utf-8` |
| `ALLOWED_ORIGINS` | ❌ | `https://www.youtube.com,...` | CORS許可オリジン | カンマ区切りURL |

## 📁 .envファイルの作成

### 1. サンプル.envファイル

```bash
# YouTube Transcript Extractor - 環境変数設定

# === APIキー類 ===
# YouTube Data API v3のAPIキー（必須）
YOUTUBE_API_KEY=AIzaSyABCDEF1234567890abcdef1234567890A

# Google Gemini AIのAPIキー（必須）
GEMINI_API_KEY=AIzaSyABCDEF1234567890abcdef1234567890B

# /extractエンドポイント認証用トークン（必須）
TRANSCRIPT_API_TOKEN=hybrid-yt-token-2024

# === 設定値 ===
# サーバーポート番号
PORT=8765

# 字幕最大文字数制限
MAX_TRANSCRIPT_LENGTH=50000

# Python文字エンコーディング
PYTHONIOENCODING=utf-8

# CORS許可オリジン
ALLOWED_ORIGINS=https://www.youtube.com,https://m.youtube.com,https://music.youtube.com
```

### 2. ファイル作成手順

```bash
# プロジェクトディレクトリに移動
cd C:\Users\Tenormusica\youtube_transcript_webapp

# .envファイルを作成（メモ帳で編集）
notepad .env

# または PowerShellで直接作成
echo "# YouTube Transcript Extractor - 環境変数設定" > .env
echo "YOUTUBE_API_KEY=YOUR_YOUTUBE_API_KEY_HERE" >> .env
echo "GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE" >> .env
echo "TRANSCRIPT_API_TOKEN=hybrid-yt-token-2024" >> .env
```

## 🔧 自動環境変数検証ツール

### 使用方法

```bash
# 検証ツールを実行
python env_validator.py

# 自動修正機能付きで実行
python env_validator.py
# 修正が必要な場合は 'y' を入力
```

### 機能一覧

- ✅ **必須環境変数チェック**: 全ての必須変数が設定されているか確認
- ✅ **値の妥当性検証**: APIキーの形式、ポート番号の範囲など
- ✅ **自動修正機能**: 不足している変数をデフォルト値で自動追加
- ✅ **バックアップ作成**: 修正時に元のファイルをバックアップ
- ✅ **詳細ログ**: 各検証ステップの詳細情報を表示

## 📊 API キー取得手順

### YouTube API Key

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. プロジェクトを作成または選択
3. 「APIとサービス」→「有効なAPI」で **YouTube Data API v3** を有効化
4. 「認証情報」→「認証情報を作成」→「APIキー」を選択
5. 作成されたAPIキーをコピー（39文字、`AIza`で始まる）

### Gemini API Key

1. [Google AI Studio](https://makersuite.google.com/app/apikey) にアクセス
2. 「Create API Key」をクリック
3. プロジェクトを選択（または新規作成）
4. 生成されたAPIキーをコピー（39文字、`AIza`で始まる）

## 🚨 トラブルシューティング

### 401 UNAUTHORIZED エラー

**症状**: `/extract` エンドポイントで認証エラー
```
Failed to load resource: the server responded with a status of 401 (UNAUTHORIZED)
```

**原因**: `TRANSCRIPT_API_TOKEN` が設定されていない

**解決方法**:
```bash
# .envファイルに追加
echo "TRANSCRIPT_API_TOKEN=hybrid-yt-token-2024" >> .env

# サービスを再起動
python app.py
```

### API制限エラー

**症状**: YouTube API呼び出しで quota exceeded エラー

**原因**: YouTube API の1日あたりのクォータ制限（10,000 units/day）に達している

**解決方法**:
- Google Cloud Console でクォータ制限を確認
- 必要に応じて課金を有効化してクォータを増加

### 文字化けエラー

**症状**: 日本語テキストが正しく表示されない

**原因**: 文字エンコーディングが正しく設定されていない

**解決方法**:
```bash
# .envファイルに追加
echo "PYTHONIOENCODING=utf-8" >> .env

# または環境変数を直接設定
set PYTHONIOENCODING=utf-8
python app.py
```

## ✅ 設定確認チェックリスト

起動前に以下を確認してください：

- [ ] `.env` ファイルが存在する
- [ ] `YOUTUBE_API_KEY` が設定されている（39文字、`AIza`開始）
- [ ] `GEMINI_API_KEY` が設定されている（39文字、`AIza`開始）
- [ ] `TRANSCRIPT_API_TOKEN` が設定されている（8文字以上）
- [ ] ポート8765が他のプロセスで使用されていない
- [ ] インターネット接続が有効

## 🔄 自動起動時検証

アプリケーションは起動時に自動で環境変数を検証し、問題があれば自動修正を試行します：

```
🔍 Starting YouTube Transcript Extractor with environment validation...
✅ 全ての環境変数が正常に設定されています
INFO:__main__:Starting local development server on port 8765
```

問題がある場合：
```
⚠️ 環境変数に問題が検出されました - 自動修正を試行中...
📋 バックアップ作成: .env.backup.20250815_221430
✅ 3個の環境変数を追加しました。
🔄 変更を反映するためにサービスを再起動してください。
```

## 🛡️ セキュリティ注意事項

- ✅ `.env` ファイルを Git リポジトリにコミットしないでください
- ✅ `.gitignore` に `.env` を追加してください
- ✅ APIキーは定期的に再生成してください
- ✅ 本番環境では環境変数を暗号化して保存してください
- ✅ `TRANSCRIPT_API_TOKEN` は推測しにくい値に変更してください

---

**最終更新**: 2025-08-15  
**バージョン**: YouTube Transcript Extractor v1.0