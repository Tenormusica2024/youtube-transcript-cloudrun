# YouTube Transcript App Quick Launcher
# 一発起動＆ブラウザオープン

Write-Host "🚀 YouTube Transcript App Quick Launcher" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

# カレントディレクトリを設定
Set-Location "C:\Users\Tenormusica\youtube_transcript_webapp"

# ポート5000の使用状況チェック
function Test-Port5000 {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port 5000 -InformationLevel Quiet -WarningAction SilentlyContinue
        return $connection
    }
    catch {
        return $false
    }
}

# アプリが動作中かチェック
if (Test-Port5000) {
    Write-Host "✅ App is already running!" -ForegroundColor Green
    Write-Host "🌐 Opening browser..." -ForegroundColor Cyan
    Start-Process "http://localhost:5000/"
    Write-Host "✨ Ready to use!" -ForegroundColor Green
    exit
}

Write-Host "⚙️ Starting YouTube Transcript App..." -ForegroundColor Yellow

# アプリケーション起動
$process = Start-Process -FilePath "python" -ArgumentList "app.py" -WindowStyle Minimized -PassThru
Write-Host "📦 Process started (PID: $($process.Id))" -ForegroundColor Blue

# 起動待機
Write-Host "⏳ Waiting for server to start..." -ForegroundColor Yellow
$maxWait = 20
$waited = 0

while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 1
    $waited++
    
    if (Test-Port5000) {
        Write-Host "✅ Server started successfully!" -ForegroundColor Green
        Write-Host "🌐 Opening browser..." -ForegroundColor Cyan
        Start-Sleep -Seconds 1
        Start-Process "http://localhost:5000/"
        Write-Host "✨ YouTube Transcript App is ready!" -ForegroundColor Green
        Write-Host "📍 Access URL: http://localhost:5000/" -ForegroundColor White
        exit
    }
    
    Write-Host "⏳ Starting... ($waited/$maxWait seconds)" -ForegroundColor Yellow
}

# 起動失敗時
Write-Host "❌ Failed to start within $maxWait seconds" -ForegroundColor Red
Write-Host "🔍 Checking Python processes..." -ForegroundColor Yellow
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Format-Table -AutoSize

Write-Host "💡 Try running manually:" -ForegroundColor Cyan
Write-Host "   cd C:\Users\Tenormusica\youtube_transcript_webapp" -ForegroundColor White
Write-Host "   python app.py" -ForegroundColor White