@echo off
echo 🚀 YouTube字幕抽出ツール - ngrokトンネル起動

REM ngrokの存在確認
where ngrok >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ エラー: ngrokが見つかりません
    echo ngrokをインストールしてください: https://ngrok.com/download
    pause
    exit /b 1
)

echo 📡 ngrokトンネルを起動中... (ポート8085)
echo.
echo ⚠️  注意: このウィンドウを閉じるとngrokトンネルも停止します
echo.

REM ngrokでポート8085を公開
ngrok http 8085 --log=stdout

pause