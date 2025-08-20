@echo off
chcp 65001 > nul
title YouTube字幕抽出ツール（ハイブリッド版）

echo.
echo ============================================
echo  YouTube字幕抽出ツール（ハイブリッド版）
echo ============================================
echo  ローカル抽出 + Cloud Run AI整形・要約
echo ============================================
echo.

cd /d "%~dp0"

echo Pythonスクリプトを実行中...
python hybrid_transcript_tool.py

echo.
echo ============================================
echo 処理が完了しました。
echo ============================================
pause