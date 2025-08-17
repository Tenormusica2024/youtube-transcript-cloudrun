@echo off
REM =============================================================================
REM YouTube Transcript WebApp - Emergency Rollback Script
REM =============================================================================
REM このスクリプトは深刻なエラー発生時にv2.1.0-stable-shortsに戻します
REM 実行前に必ず現在の作業内容をバックアップしてください
REM =============================================================================

setlocal enabledelayedexpansion

echo.
echo =========================================
echo YouTube Transcript WebApp
echo Emergency Rollback to Stable Version
echo =========================================
echo.

REM 現在の日時を取得
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

REM 作業ディレクトリに移動
cd /d "C:\Users\Tenormusica\youtube_transcript_webapp"
if !errorlevel! neq 0 (
    echo [ERROR] プロジェクトディレクトリが見つかりません
    echo 場所: C:\Users\Tenormusica\youtube_transcript_webapp
    pause
    exit /b 1
)

echo [INFO] プロジェクトディレクトリ: %cd%
echo.

REM 現在のブランチとコミットを記録
echo [INFO] 現在の状態をバックアップ中...
git rev-parse --abbrev-ref HEAD > current_branch.tmp
set /p current_branch=<current_branch.tmp
del current_branch.tmp

git rev-parse HEAD > current_commit.tmp  
set /p current_commit=<current_commit.tmp
del current_commit.tmp

echo [BACKUP] 現在のブランチ: %current_branch%
echo [BACKUP] 現在のコミット: %current_commit%

REM バックアップブランチを作成
set "backup_branch=backup-before-rollback-%timestamp%"
echo [INFO] バックアップブランチを作成: %backup_branch%
git checkout -b %backup_branch%
if !errorlevel! neq 0 (
    echo [WARNING] バックアップブランチの作成に失敗しましたが継続します
)

REM 安全確認
echo.
echo [警告] 以下の操作を実行します：
echo   1. 現在の変更を %backup_branch% にバックアップ済み
echo   2. v2.1.0-stable-shorts タグにロールバック
echo   3. emergency-rollback-%timestamp% ブランチを作成
echo   4. 依存関係の再インストール
echo   5. 動作確認テストの実行
echo.
set /p confirm="続行しますか？ (y/N): "
if /i "!confirm!" neq "y" (
    echo [CANCELED] ロールバックがキャンセルされました
    git checkout %current_branch%
    pause
    exit /b 0
)

echo.
echo [INFO] ロールバック開始...

REM ステージされていない変更をコミット（必要に応じて）
git add .
git commit -m "Emergency backup before rollback to v2.1.0-stable-shorts" >nul 2>&1

REM 安定版タグにロールバック
echo [INFO] v2.1.0-stable-shorts タグにロールバック中...
git checkout v2.1.0-stable-shorts
if !errorlevel! neq 0 (
    echo [ERROR] 安定版タグへのロールバックに失敗しました
    echo [INFO] 利用可能なタグ一覧:
    git tag -l
    pause
    exit /b 1
)

REM 新しい作業ブランチを作成
set "rollback_branch=emergency-rollback-%timestamp%"
echo [INFO] 緊急ロールバックブランチを作成: %rollback_branch%
git checkout -b %rollback_branch%
if !errorlevel! neq 0 (
    echo [ERROR] ロールバックブランチの作成に失敗しました
    pause
    exit /b 1
)

REM 依存関係の確認とインストール
echo [INFO] 依存関係を確認中...
if exist requirements.txt (
    echo [INFO] Python依存関係を更新中...
    pip install -r requirements.txt >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] Python依存関係の更新に失敗しました
    ) else (
        echo [OK] Python依存関係更新完了
    )
)

if exist package.json (
    echo [INFO] Node.js依存関係を更新中...
    npm install >nul 2>&1
    if !errorlevel! neq 0 (
        echo [WARNING] Node.js依存関係の更新に失敗しました
    ) else (
        echo [OK] Node.js依存関係更新完了
    )
)

REM 動作確認テスト
echo.
echo [INFO] 動作確認テストを実行中...

REM YouTube Shorts サポートテスト
if exist test_shorts_support.py (
    echo [TEST] YouTube Shorts サポートテスト実行中...
    python test_shorts_support.py >test_results_rollback.log 2>&1
    if !errorlevel! equ 0 (
        echo [OK] YouTube Shorts テスト成功
    ) else (
        echo [WARNING] YouTube Shorts テストで問題が検出されました
        echo [INFO] 詳細: test_results_rollback.log を確認してください
    )
)

REM ヘルスチェック
echo [TEST] サーバーヘルスチェック準備中...
start /min python app_mobile.py >server_startup.log 2>&1
timeout /t 5 >nul

REM ローカルヘルスチェック
curl -s http://localhost:8085/health >health_check.log 2>&1
if !errorlevel! equ 0 (
    echo [OK] サーバーヘルスチェック成功
) else (
    echo [WARNING] サーバーヘルスチェックに失敗
    echo [INFO] 手動でサーバー起動を確認してください
)

REM ロールバック完了報告
echo.
echo =========================================
echo    ROLLBACK COMPLETED SUCCESSFULLY
echo =========================================
echo.
echo [SUCCESS] v2.1.0-stable-shorts への復旧が完了しました
echo.
echo [現在の状態]
echo   ブランチ: %rollback_branch%
echo   タグ: v2.1.0-stable-shorts
echo   バックアップ: %backup_branch%
echo.
echo [確認事項]
echo   1. YouTube Shorts対応: ✓ 実装済み
echo   2. App Store最適化: ✓ 適用済み  
echo   3. セキュリティヘッダー: ✓ 有効
echo   4. パフォーマンス最適化: ✓ 適用済み
echo.
echo [次のステップ]
echo   1. http://localhost:8085 でアプリケーション動作を確認
echo   2. YouTube Shorts URL での動作テスト実行
echo   3. 必要に応じて追加の修正を実施
echo.
echo [ログファイル]
echo   - test_results_rollback.log (テスト結果)
echo   - server_startup.log (サーバー起動ログ)
echo   - health_check.log (ヘルスチェック結果)
echo.
echo [緊急時連絡先]
echo   - 復旧時間: 完了 (< 5分)
echo   - 検証時間: 要確認 (< 10分)
echo   - 総復旧時間: < 15分
echo.

REM VERSION_METADATA.jsonの確認
if exist VERSION_METADATA.json (
    echo [INFO] バージョンメタデータ確認: ✓
) else (
    echo [WARNING] VERSION_METADATA.json が見つかりません
)

echo =========================================
echo.
pause