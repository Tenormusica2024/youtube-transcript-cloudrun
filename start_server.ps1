# YouTube字幕抽出ツール - 起動スクリプト (構文修正版)
Write-Host "🎬 YouTube字幕抽出ツール起動中..." -ForegroundColor Cyan

# 環境変数設定
$env:FLASK_ENV = 'development'
Write-Host "✅ 開発モードに設定済み" -ForegroundColor Green

# 残骸プロセス停止
Write-Host "🔧 既存プロセスを停止中..." -ForegroundColor Yellow
Start-Process -FilePath "taskkill" -ArgumentList "/F", "/IM", "python.exe", "/T" -WindowStyle Hidden -Wait -ErrorAction SilentlyContinue
Write-Host "✅ プロセス停止完了" -ForegroundColor Green

# ポート確認
$portCheck = Get-NetTCPConnection -State Listen -LocalPort 8085 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "⚠️  ポート8085が使用中です。手動で停止してください:" -ForegroundColor Yellow
    $portCheck | ForEach-Object {
        Write-Host "   taskkill /PID $($_.OwningProcess) /F" -ForegroundColor Red
    }
    Read-Host "停止完了後、Enterを押してください"
} else {
    Write-Host "✅ ポート8085は利用可能です" -ForegroundColor Green
}

# サーバー起動
Write-Host ""
Write-Host "🚀 サーバー起動中..." -ForegroundColor Yellow
Write-Host "📱 アクセスURL: http://127.0.0.1:8085" -ForegroundColor Green
Write-Host "🏥 ヘルスチェック: http://127.0.0.1:8085/health" -ForegroundColor Green
Write-Host "⏹️  停止するには Ctrl+C を押してください" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Cyan

# 直接実行
python app_mobile.py