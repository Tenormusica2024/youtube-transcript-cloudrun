# YouTube字幕抽出ツール復旧手順

## GitHubコミット 9a00083d73bf42e65c8a7f89265f8f8f4c1d47ef に基づく復旧完了

### ✅ 修正済み内容

1. **performance_optimizerフォールバック処理** - ImportError対策
2. **Flask初期化の改善** - template/staticフォルダパス明示
3. **HTTP固定起動** - HTTPS/SSL設定を無効化してHTTPで安定動作
4. **依存関係の整理** - 必要最小限のパッケージ構成

### 🚀 起動方法（推奨順）

#### 方法1: PowerShellスクリプト（推奨）
```powershell
# 管理者権限でPowerShellを開き以下を実行
cd C:\Users\Tenormusica\youtube_transcript_webapp
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\restore_and_start.ps1
```

#### 方法2: 手動コマンド実行
```powershell
# 1. 残骸プロセス停止
taskkill /F /IM python.exe /T
taskkill /F /IM node.exe /T

# 2. ポート確認
netstat -ano | findstr :8085

# 3. 環境変数設定
$env:FLASK_ENV = 'development'

# 4. サーバー起動
cd C:\Users\Tenormusica\youtube_transcript_webapp
py -3 app_mobile.py
```

#### 方法3: バックグラウンド起動（ログ出力版）
```powershell
cd C:\Users\Tenormusica\youtube_transcript_webapp
$env:FLASK_ENV = 'development'
py -3 app_mobile.py 1> run.log 2>&1 &
```

### 📊 動作確認

1. **ポート確認**: `Get-NetTCPConnection -State Listen -LocalPort 8085`
2. **ヘルスチェック**: `iwr http://127.0.0.1:8085/health -UseBasicParsing`
3. **ブラウザアクセス**: http://127.0.0.1:8085

### 🎯 アクセスURL

- **メインページ**: http://127.0.0.1:8085
- **ヘルスチェック**: http://127.0.0.1:8085/health
- **詳細ステータス**: http://127.0.0.1:8085/api/status
- **QRコード生成**: http://127.0.0.1:8085/qr-code

### 🔧 トラブルシューティング

#### エラー: ポート8085が使用中
```powershell
# 使用中のプロセスを確認
Get-NetTCPConnection -State Listen -LocalPort 8085
# プロセスを強制停止
taskkill /PID <PID番号> /F
```

#### エラー: 依存関係が見つからない
```powershell
# 必要最小限のパッケージをインストール
py -3 -m pip install flask flask-cors youtube-transcript-api qrcode python-dotenv google-generativeai google-api-python-client
```

#### エラー: performance_optimizer関連
- 既に修正済み（フォールバック処理実装）
- performance_optimizer.pyファイルも存在確認済み

### 📱 スマホアクセス設定（ngrok使用）

1. **ngrok起動**: `start_ngrok_youtube.bat`
2. **QRコード取得**: http://127.0.0.1:8085/qr-code
3. **スマホでQRコードスキャン**

### 🎨 UI仕様

- **デザイン**: 赤基調の水面反射エフェクト
- **レスポンシブ**: スマホ・タブレット対応
- **機能**: YouTube字幕抽出、AI整形、要約生成、QRコード対応

### 📝 ログ確認

起動時に問題がある場合は以下のファイルを確認：
- `run.log` - 標準出力
- `run_error.log` - エラー出力

### 🌐 Cloud Run デプロイ

ローカル動作確認後、Cloud Runへのデプロイは以下で実行：
```bash
./deploy.sh
```

## ⚠️ 重要事項

- **FLASK_ENV=development** でHTTP動作（本番環境ではHTTPS）
- **ポート8085固定** - ngrokやCloud Runは別ポート使用
- **AIキー設定** - 環境変数 `GEMINI_API_KEY` でAI機能有効化

## 復旧完了ステータス: ✅ 全て完了

- [x] GitHubコミットからの復元
- [x] performance_optimizerフォールバック実装
- [x] HTTP固定起動設定
- [x] 起動スクリプト作成
- [x] 動作確認手順整備