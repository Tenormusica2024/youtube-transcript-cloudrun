@echo off
echo =====================================================
echo 修正版 YouTube字幕抽出ツール起動スクリプト
echo =====================================================

REM FLASK_ENVを開発モードに設定
set FLASK_ENV=development

REM 現在のディレクトリに移動
cd /d "%~dp0"

echo ✅ FLASK_ENV=development に設定済み
echo ✅ performance_optimizer フォールバック追加済み
echo ✅ HTTP固定起動（SSL無効）

echo.
echo 🚀 修正版サーバーを起動中...
echo ポート: 8085 (HTTP)
echo URL: http://127.0.0.1:8085
echo.

REM ログファイルに出力してタイムアウト回避
python app_mobile.py 1> run.log 2>&1

echo.
echo 📴 サーバーが停止しました
echo 📋 ログファイル: run.log を確認してください
pause