# ngrok固定URL版セットアップガイド

## 🚨 重要: デモ版データ完全削除済み

✅ **完了済み:**
- `demo_run.py` ファイル削除
- `showDemoResults` 関数削除 
- 全デモ関連データ除去
- v1.5.1-clean統一済み

## ngrokトークン設定が必要

現在のngrokトークンが無効です。新しいトークンを取得してください。

### 手順:

1. **ngrokダッシュボードにアクセス:**
   https://dashboard.ngrok.com/get-started/your-authtoken

2. **新しいAuthtokenをコピー**

3. **トークン設定コマンド実行:**
   ```bash
   "C:\Users\Tenormusica\ngrok.exe" authtoken YOUR_NEW_TOKEN_HERE
   ```

4. **ngrok起動 (動的URL版):**
   ```bash
   "C:\Users\Tenormusica\ngrok.exe" http 8085
   ```

## 現在のシステム状況

✅ **Flask App**: http://127.0.0.1:8085 (正常動作中)
❌ **ngrok**: トークン無効のため停止中
✅ **デモ版削除**: 完全削除済み

## 起動用スクリプト

- `start_ngrok.py` - Python版管理スクリプト
- `start_ngrok_simple.bat` - バッチ版簡易起動
- `ngrok_config.yml` - ngrok設定ファイル

## 固定URL版について

固定URL(yt-transcript.ngrok.io)を使用するには:
- ngrok有料プラン必要
- DNS CNAME設定が必要
- 現在は`--hostname`フラグが非推奨

**推奨:** 動的URL版で運用し、URLが変わった際に通知