@echo off
title YouTube Transcript Tool - Production Server
color 0A
echo.
echo ==============================================================================
echo                     YouTube Transcript Tool - Production v1.3.11
echo ==============================================================================
echo.
echo Starting production server...
echo Server will be available at: http://127.0.0.1:8080
echo.
cd /d "%~dp0"
python production_server.py
echo.
echo Server stopped. Press any key to exit...
pause > nul