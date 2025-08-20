# YouTube字幕抽出ツール - 修正版起動スクリプト
Write-Host "=====================================================" -ForegroundColor Yellow
Write-Host "修正版 YouTube字幕抽出ツール PowerShell起動" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Yellow

# FLASK_ENVを開発モードに設定
$env:FLASK_ENV = 'development'
Write-Host "✅ FLASK_ENV=development に設定済み" -ForegroundColor Green

# ディレクトリ移動
Set-Location "C:\Users\Tenormusica\youtube_transcript_webapp"

Write-Host "✅ performance_optimizer フォールバック追加済み" -ForegroundColor Green
Write-Host "✅ HTTP固定起動（SSL無効）" -ForegroundColor Green
Write-Host ""

Write-Host "🚀 修正版サーバーを起動中..." -ForegroundColor Cyan
Write-Host "ポート: 8085 (HTTP)" -ForegroundColor White
Write-Host "URL: http://127.0.0.1:8085" -ForegroundColor White
Write-Host ""

# バックグラウンドでログ出力しつつ起動
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "app_mobile.py" -RedirectStandardOutput "run.log" -RedirectStandardError "run_error.log"

# 5秒待機してポート確認
Start-Sleep -Seconds 5

Write-Host "🔍 ポート確認中..." -ForegroundColor Cyan
try {
    $connection = Get-NetTCPConnection -State Listen -LocalPort 8085 -ErrorAction SilentlyContinue
    if ($connection) {
        Write-Host "✅ ポート8085でLISTEN中" -ForegroundColor Green
        
        Write-Host "🌐 ヘルスチェック実行中..." -ForegroundColor Cyan
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8085/health" -UseBasicParsing -TimeoutSec 10
            Write-Host "✅ ヘルスチェック成功: $($response.StatusCode)" -ForegroundColor Green
            Write-Host "📱 ブラウザで http://127.0.0.1:8085 を開いてください" -ForegroundColor Yellow
        }
        catch {
            Write-Host "⚠️  ヘルスチェック失敗: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "📋 run.log と run_error.log を確認してください" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "❌ ポート8085でLISTENしていません" -ForegroundColor Red
        Write-Host "📋 run.log と run_error.log を確認してください" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ ポート確認エラー: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📋 ログファイル:" -ForegroundColor Cyan
Write-Host "   出力: run.log" -ForegroundColor White
Write-Host "   エラー: run_error.log" -ForegroundColor White
Write-Host ""
Write-Host "🛑 サーバーを停止するには Ctrl+C を押してください" -ForegroundColor Yellow

# ログ表示待機
Read-Host "Enterキーで終了"