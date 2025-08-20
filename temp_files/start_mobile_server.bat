@echo off
echo ======================================================
echo YouTube字幕抽出ツール - スマホ版サーバー起動
echo ======================================================
echo.

cd /d "C:\Users\Tenormusica\youtube_transcript_webapp"

echo 必要なパッケージをインストール中...
pip install qrcode[pil] flask flask-cors python-dotenv youtube-transcript-api google-generativeai google-api-python-client > nul 2>&1

echo.
echo 🎬 YouTube Transcript Extractor - Mobile Version
echo ======================================================
echo 🚀 サーバーを起動中... (ポート: 8085)
echo.
echo 📱 アクセスURL:
echo    ローカル: http://localhost:8085
echo    スマホ: 同じWi-Fiネットワークから http://[あなたのIP]:8085
echo.
echo 🔥 ngrok公開アクセスは別途 start_ngrok_youtube.bat を実行
echo ======================================================
echo.

python app_mobile.py

pause