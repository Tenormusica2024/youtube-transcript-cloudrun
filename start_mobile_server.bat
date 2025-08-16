@echo off
cd /d "%~dp0"

echo 🚀 YouTube字幕抽出ツール（スマホ対応版）を起動中...
echo.

REM 仮想環境の確認
if exist "venv\Scripts\activate.bat" (
    echo 📦 仮想環境を有効化中...
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  仮想環境が見つかりません - システムPythonを使用
)

REM 必要なパッケージのインストール確認
echo 📋 パッケージ依存関係を確認中...
pip install -q qrcode[pil] flask flask-cors python-dotenv google-generativeai google-api-python-client youtube-transcript-api

echo.
echo 🌐 サーバー起動中...
echo 📱 ローカルアクセス: http://127.0.0.1:8085
echo 🔗 ネットワークアクセス: http://[IPアドレス]:8085
echo.
echo ⚠️  注意: ngrokを使用する場合は、別ターミナルで start_ngrok_youtube.bat を実行してください
echo.

REM スマホ対応サーバーを起動
python app_mobile.py

pause