# YouTube字幕抽出ツール復旧 & 起動スクリプト (修正版)
# GitHubコミット 9a00083d73bf42e65c8a7f89265f8f8f4c1d47ef 対応版

Write-Host "=========================================================" -ForegroundColor Cyan
Write-Host "🎬 YouTube字幕抽出ツール - 復旧プロセス開始" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# 現在のディレクトリを設定
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $scriptDir
Write-Host "📂 作業ディレクトリ: $scriptDir" -ForegroundColor Green

# 1. 残骸プロセスを停止
Write-Host "`n🔧 Step 1: 残骸プロセスを停止中..." -ForegroundColor Yellow
try {
    $pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcesses) {
        $pythonProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Pythonプロセス停止完了" -ForegroundColor Green
    }
    
    $nodeProcesses = Get-Process node -ErrorAction SilentlyContinue  
    if ($nodeProcesses) {
        $nodeProcesses | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Nodeプロセス停止完了" -ForegroundColor Green
    }
    
    Start-Process -FilePath "taskkill" -ArgumentList "/F", "/IM", "python.exe", "/T" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Start-Process -FilePath "taskkill" -ArgumentList "/F", "/IM", "node.exe", "/T" -WindowStyle Hidden -ErrorAction SilentlyContinue
    Write-Host "✅ プロセス停止完了" -ForegroundColor Green
}
catch {
    Write-Host "⚠️  プロセス停止中にエラー（継続可能）: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 2. ポート8085を確認・解放
Write-Host "`n🔧 Step 2: ポート8085の状態確認..." -ForegroundColor Yellow
try {
    $portInUse = Get-NetTCPConnection -State Listen -LocalPort 8085 -ErrorAction SilentlyContinue
    if ($portInUse) {
        Write-Host "⚠️  ポート8085が使用中。プロセスを停止中..." -ForegroundColor Yellow
        foreach ($connection in $portInUse) {
            $processId = $connection.OwningProcess
            Write-Host "   PID $processId を停止中..." -ForegroundColor Gray
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Host "   ✅ PID $processId 停止完了" -ForegroundColor Green
            }
            catch {
                Write-Host "   ❌ プロセス停止失敗: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        Start-Sleep -Seconds 2
    }

    $portStatus = Get-NetTCPConnection -State Listen -LocalPort 8085 -ErrorAction SilentlyContinue
    if ($portStatus) {
        Write-Host "❌ ポート8085がまだ使用中です。手動で対処が必要です。" -ForegroundColor Red
        Write-Host "   以下のコマンドで強制停止してください:" -ForegroundColor Red
        foreach ($connection in $portStatus) {
            Write-Host "   taskkill /PID $($connection.OwningProcess) /F" -ForegroundColor Red
        }
        Read-Host "対処完了後、Enterキーを押してください"
    }
    else {
        Write-Host "✅ ポート8085は利用可能です" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️  ポート確認でエラー: $($_.Exception.Message)" -ForegroundColor Yellow
}

# 3. 環境変数設定
Write-Host "`n🔧 Step 3: 環境変数設定..." -ForegroundColor Yellow
$env:FLASK_ENV = 'development'
$env:FLASK_DEBUG = '0'
Write-Host "✅ FLASK_ENV=development, FLASK_DEBUG=0 設定完了" -ForegroundColor Green

# 4. 依存関係確認
Write-Host "`n🔧 Step 4: Python依存関係確認..." -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Write-Host "📦 requirements.txtを発見。依存関係をインストール中..." -ForegroundColor Blue
    try {
        $pipResult = & py -3 -m pip install -r requirements.txt --quiet --user 2>&1
        Write-Host "✅ 依存関係インストール完了" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  依存関係インストールでエラー（継続可能）: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}
else {
    Write-Host "📦 最小限の依存関係をインストール中..." -ForegroundColor Blue
    try {
        $packages = @("flask", "flask-cors", "youtube-transcript-api", "qrcode", "python-dotenv", "google-generativeai", "google-api-python-client")
        foreach ($package in $packages) {
            Write-Host "   インストール中: $package" -ForegroundColor Gray
            & py -3 -m pip install $package --quiet --user 2>&1 | Out-Null
        }
        Write-Host "✅ 最小依存関係インストール完了" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠️  依存関係インストールでエラー（継続可能）: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# 5. app_mobile.py存在確認
Write-Host "`n🔧 Step 5: app_mobile.py確認..." -ForegroundColor Yellow
if (Test-Path "app_mobile.py") {
    $fileSize = (Get-Item "app_mobile.py").Length
    Write-Host "✅ app_mobile.py確認済み（サイズ: $fileSize bytes）" -ForegroundColor Green
    
    # 修正内容の確認
    $content = Get-Content "app_mobile.py" -Raw
    if ($content -match "Performance optimizer with fallback" -and $content -match "app\.run\(host=`"0\.0\.0\.0`", port=8085, debug=False\)") {
        Write-Host "✅ 修正内容確認済み（performance_optimizerフォールバック + HTTP固定）" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  修正内容が不完全な可能性があります" -ForegroundColor Yellow
    }
}
else {
    Write-Host "❌ app_mobile.pyが見つかりません！" -ForegroundColor Red
    exit 1
}

# 6. サーバー起動
Write-Host "`n🚀 Step 6: サーバー起動中..." -ForegroundColor Yellow
Write-Host "📝 ログは画面に直接表示されます" -ForegroundColor Blue

try {
    # バックグラウンドでサーバー起動
    $job = Start-Job -ScriptBlock {
        param($workDir)
        Set-Location $workDir
        $env:FLASK_ENV = 'development'
        $env:FLASK_DEBUG = '0'
        & py -3 app_mobile.py 2>&1
    } -ArgumentList $scriptDir

    # 起動待機
    Write-Host "⏳ サーバー起動を待機中（最大20秒）..." -ForegroundColor Blue
    $maxWait = 20
    $waited = 0
    $serverStarted = $false
    
    do {
        Start-Sleep -Seconds 1
        $waited++
        $serverCheck = Get-NetTCPConnection -State Listen -LocalPort 8085 -ErrorAction SilentlyContinue
        if ($serverCheck) {
            Write-Host "`n✅ サーバーがポート8085でリスニング開始！（$waited 秒後）" -ForegroundColor Green
            $serverStarted = $true
            break
        }
        Write-Host "." -NoNewline -ForegroundColor Gray
    } while ($waited -lt $maxWait)

    if (-not $serverStarted) {
        Write-Host "`n⚠️  20秒経過してもサーバーが起動しませんでした" -ForegroundColor Yellow
        Write-Host "   ジョブ状態を確認中..." -ForegroundColor Blue
        
        # ジョブの出力を確認
        $jobOutput = Receive-Job $job -ErrorAction SilentlyContinue
        if ($jobOutput) {
            Write-Host "📝 サーバー出力:" -ForegroundColor Blue
            $jobOutput | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }
        
        Write-Host "`n🔍 手動確認が必要です。以下のコマンドで状況を確認してください:" -ForegroundColor Yellow
        Write-Host "   Get-NetTCPConnection -State Listen -LocalPort 8085" -ForegroundColor Gray
        Write-Host "   py -3 app_mobile.py" -ForegroundColor Gray
    }
    else {
        # 7. ヘルスチェック
        Write-Host "`n🔧 Step 7: ヘルスチェック実行..." -ForegroundColor Yellow
        Start-Sleep -Seconds 2  # サーバー完全起動待機
        
        try {
            $healthResponse = Invoke-WebRequest -Uri "http://127.0.0.1:8085/health" -UseBasicParsing -TimeoutSec 10
            if ($healthResponse.StatusCode -eq 200) {
                Write-Host "✅ ヘルスチェック成功！" -ForegroundColor Green
                $responseText = $healthResponse.Content
                if ($responseText.Length -gt 100) {
                    $responseText = $responseText.Substring(0, 100) + "..."
                }
                Write-Host "📊 レスポンス: $responseText" -ForegroundColor Gray
            }
            else {
                Write-Host "⚠️  ヘルスチェック失敗（ステータス: $($healthResponse.StatusCode)）" -ForegroundColor Yellow
            }
        }
        catch {
            Write-Host "⚠️  ヘルスチェック接続エラー: $($_.Exception.Message)" -ForegroundColor Yellow
            Write-Host "   サーバーはポートでリスニング中ですが、HTTP応答に問題がある可能性があります" -ForegroundColor Yellow
        }
        
        # 8. 最終確認とブラウザ起動
        Write-Host "`n=========================================================" -ForegroundColor Cyan
        Write-Host "🎉 復旧プロセス完了！" -ForegroundColor Cyan
        Write-Host "=========================================================" -ForegroundColor Cyan
        Write-Host "📱 ローカルアクセス: http://127.0.0.1:8085" -ForegroundColor Green
        Write-Host "🏥 ヘルスチェック: http://127.0.0.1:8085/health" -ForegroundColor Green
        Write-Host "📊 ステータス: http://127.0.0.1:8085/api/status" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 ブラウザを自動起動します..." -ForegroundColor Blue
        
        try {
            Start-Process "http://127.0.0.1:8085"
            Write-Host "✅ ブラウザ起動完了" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠️  ブラウザ自動起動失敗。手動でアクセスしてください: http://127.0.0.1:8085" -ForegroundColor Yellow
        }
        
        Write-Host "`n🔄 サーバーを停止するには Ctrl+C を押してください" -ForegroundColor Blue
        Write-Host "📝 サーバーログを確認するには以下を実行:" -ForegroundColor Blue
        Write-Host "   Receive-Job -Id $($job.Id) -Keep" -ForegroundColor Gray
        
        # サーバーログを継続表示
        Write-Host "`n📊 サーバーログ（Ctrl+Cで停止）:" -ForegroundColor Blue
        try {
            while ($true) {
                $logOutput = Receive-Job $job -ErrorAction SilentlyContinue
                if ($logOutput) {
                    $logOutput | ForEach-Object { Write-Host $_ -ForegroundColor White }
                }
                Start-Sleep -Seconds 1
            }
        }
        catch {
            Write-Host "`n👋 スクリプト終了" -ForegroundColor Yellow
        }
    }
}
catch {
    Write-Host "❌ サーバー起動でエラー: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   手動起動を試してください: py -3 app_mobile.py" -ForegroundColor Yellow
}

Write-Host "`n⚠️  スクリプト終了後もサーバーはバックグラウンドで稼働中です" -ForegroundColor Yellow
Write-Host "   停止するには: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor Gray