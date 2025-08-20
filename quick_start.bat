@echo off
echo ==========================================
echo 🎬 YouTube字幕抽出ツール - 起動
echo ==========================================

REM 環境変数設定
set FLASK_ENV=development
set FLASK_DEBUG=0
echo ✅ 開発モード設定完了

REM 残骸プロセス停止
echo 🔧 既存プロセス停止中...
taskkill /F /IM python.exe /T >nul 2>&1
echo ✅ プロセス停止完了

REM サーバー起動
echo.
echo 🚀 サーバー起動中...
echo 📱 アクセスURL: http://127.0.0.1:8085
echo 🏥 ヘルスチェック: http://127.0.0.1:8085/health
echo ⏹️  停止するには Ctrl+C を押してください
echo ==========================================
echo.

python app_mobile.py