# YouTube Transcript App Auto-Start Service
# システム起動時の自動開始とヘルスチェック機能

param(
    [switch]$Install,
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Test
)

$ServiceName = "YouTubeTranscriptApp"
$AppPath = "C:\Users\Tenormusica\youtube_transcript_webapp"
$PythonScript = "app.py"
$Port = 5000
$LogFile = "$AppPath\service.log"

function Write-ServiceLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
}

function Test-ServiceRunning {
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -ErrorAction SilentlyContinue
        return $connection
    }
    catch {
        return $false
    }
}

function Start-YouTubeTranscriptApp {
    Write-ServiceLog "Starting YouTube Transcript App..." "INFO"
    
    # 既に動作中かチェック
    if (Test-ServiceRunning) {
        Write-ServiceLog "App is already running on port $Port" "SUCCESS"
        return $true
    }
    
    try {
        # アプリケーション起動
        Push-Location $AppPath
        $process = Start-Process -FilePath "python" -ArgumentList $PythonScript -WindowStyle Minimized -PassThru
        Write-ServiceLog "Python process started with PID: $($process.Id)" "INFO"
        
        # 起動待機
        $maxWait = 30
        $waited = 0
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 1
            $waited++
            
            if (Test-ServiceRunning) {
                Write-ServiceLog "App started successfully on port $Port" "SUCCESS"
                Pop-Location
                return $true
            }
            
            Write-ServiceLog "Waiting for app to start... ($waited/$maxWait)" "INFO"
        }
        
        Write-ServiceLog "App failed to start within $maxWait seconds" "ERROR"
        Pop-Location
        return $false
    }
    catch {
        Write-ServiceLog "Error starting app: $($_.Exception.Message)" "ERROR"
        Pop-Location
        return $false
    }
}

function Stop-YouTubeTranscriptApp {
    Write-ServiceLog "Stopping YouTube Transcript App..." "INFO"
    
    try {
        # Python プロセスを停止
        $processes = Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { 
            $_.MainWindowTitle -like "*flask*" -or 
            $_.ProcessName -eq "python" -or 
            $_.ProcessName -eq "pythonw"
        }
        
        if ($processes) {
            foreach ($process in $processes) {
                try {
                    # ポート使用中のプロセスを特定して停止
                    $netstat = netstat -ano | Select-String ":$Port"
                    if ($netstat) {
                        $pid = ($netstat.ToString().Split())[-1]
                        if ($process.Id -eq $pid) {
                            $process.Kill()
                            Write-ServiceLog "Stopped process PID: $($process.Id)" "SUCCESS"
                        }
                    }
                }
                catch {
                    Write-ServiceLog "Error stopping process: $($_.Exception.Message)" "WARNING"
                }
            }
        }
        
        # 確認
        Start-Sleep -Seconds 2
        if (-not (Test-ServiceRunning)) {
            Write-ServiceLog "App stopped successfully" "SUCCESS"
            return $true
        }
        else {
            Write-ServiceLog "App may still be running" "WARNING"
            return $false
        }
    }
    catch {
        Write-ServiceLog "Error stopping app: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Install-AutoStartService {
    Write-ServiceLog "Installing auto-start service..." "INFO"
    
    try {
        # タスクスケジューラでスタートアップタスクを作成
        $taskName = "YouTube-Transcript-AutoStart"
        $action = New-ScheduledTaskAction -Execute "PowerShell" -Argument "-ExecutionPolicy Bypass -File `"$PSCommandPath`" -Start"
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Force
        Write-ServiceLog "Auto-start service installed successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-ServiceLog "Error installing auto-start service: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Uninstall-AutoStartService {
    Write-ServiceLog "Uninstalling auto-start service..." "INFO"
    
    try {
        $taskName = "YouTube-Transcript-AutoStart"
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-ServiceLog "Auto-start service uninstalled successfully" "SUCCESS"
        return $true
    }
    catch {
        Write-ServiceLog "Error uninstalling auto-start service: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

function Show-ServiceStatus {
    Write-ServiceLog "YouTube Transcript App Service Status" "INFO"
    Write-ServiceLog "=====================================" "INFO"
    
    # アプリケーション状態
    $isRunning = Test-ServiceRunning
    $status = if ($isRunning) { "RUNNING" } else { "STOPPED" }
    $statusColor = if ($isRunning) { "SUCCESS" } else { "ERROR" }
    Write-ServiceLog "Application Status: $status" $statusColor
    Write-ServiceLog "Port: $Port" "INFO"
    Write-ServiceLog "App Path: $AppPath" "INFO"
    
    # プロセス情報
    $processes = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    if ($processes) {
        Write-ServiceLog "Python Processes:" "INFO"
        foreach ($process in $processes) {
            Write-ServiceLog "  PID: $($process.Id), Name: $($process.ProcessName)" "INFO"
        }
    }
    
    # タスクスケジューラ状態
    $task = Get-ScheduledTask -TaskName "YouTube-Transcript-AutoStart" -ErrorAction SilentlyContinue
    $autoStartStatus = if ($task) { "ENABLED" } else { "DISABLED" }
    Write-ServiceLog "Auto-start: $autoStartStatus" "INFO"
    
    # アクセスURL
    if ($isRunning) {
        Write-ServiceLog "Access URL: http://localhost:$Port/" "SUCCESS"
    }
}

# メイン実行
Write-ServiceLog "YouTube Transcript App Service Manager" "INFO"

switch ($true) {
    $Install { 
        if (Install-AutoStartService) {
            Write-ServiceLog "Installation completed" "SUCCESS"
        }
    }
    $Uninstall { 
        Stop-YouTubeTranscriptApp
        if (Uninstall-AutoStartService) {
            Write-ServiceLog "Uninstallation completed" "SUCCESS"
        }
    }
    $Start { 
        if (Start-YouTubeTranscriptApp) {
            Write-ServiceLog "Start completed" "SUCCESS"
            Start-Sleep -Seconds 2
            start http://localhost:5000/
        }
    }
    $Stop { 
        if (Stop-YouTubeTranscriptApp) {
            Write-ServiceLog "Stop completed" "SUCCESS"
        }
    }
    $Status { 
        Show-ServiceStatus 
    }
    $Test {
        Write-ServiceLog "Running service test..." "INFO"
        Show-ServiceStatus
        if (-not (Test-ServiceRunning)) {
            Write-ServiceLog "Starting app for test..." "INFO"
            if (Start-YouTubeTranscriptApp) {
                Write-ServiceLog "Test completed successfully" "SUCCESS"
                start http://localhost:5000/
            }
        }
        else {
            Write-ServiceLog "Test completed - app already running" "SUCCESS"
        }
    }
    default {
        Write-ServiceLog "Usage:" "INFO"
        Write-ServiceLog "  -Install    : Install auto-start service" "INFO"
        Write-ServiceLog "  -Uninstall  : Remove auto-start service" "INFO"
        Write-ServiceLog "  -Start      : Start the application" "INFO"
        Write-ServiceLog "  -Stop       : Stop the application" "INFO"
        Write-ServiceLog "  -Status     : Show current status" "INFO"
        Write-ServiceLog "  -Test       : Test and auto-start if needed" "INFO"
    }
}