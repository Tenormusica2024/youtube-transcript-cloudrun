# YouTube字幕抽出ツール - 簡単起動スクリプト
Write-Host "🎬 YouTube字幕抽出ツール起動中..." -ForegroundColor Cyan

# 環境変数設定
$env:FLASK_ENV = 'development'
Write-Host "✅ 開発モードに設定済み" -ForegroundColor Green

# 残骸プロセス停止
try {
    taskkill /F /IM python.exe /T 2>$null
    Write-Host "✅ 既存Pythonプロセス停止完了" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  プロセス停止でエラー（継続可能）" -ForegroundColor Yellow
}

# サーバー起動
Write-Host "🚀 サーバー起動中..." -ForegroundColor Yellow
Write-Host "📱 アクセスURL: http://127.0.0.1:8085" -ForegroundColor Green
Write-Host "⏹️  停止するには Ctrl+C を押してください" -ForegroundColor Blue
Write-Host ""

# 直接実行（フォアグラウンド）
& py -3 app_mobile.py