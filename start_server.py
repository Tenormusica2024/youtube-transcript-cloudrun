#!/usr/bin/env python3
"""
Simple server starter for YouTube Transcript WebApp
"""

import os
import subprocess
import sys

# ポート設定
PORT = 8085

print(f"Starting YouTube Transcript WebApp on port {PORT}")
print(f"Current directory: {os.getcwd()}")

# 環境変数設定
os.environ["PORT"] = str(PORT)

# アプリ起動
try:
    if __name__ == "__main__":
        # app.pyを直接実行
        with open("app.py", "r", encoding="utf-8") as f:
            exec(f.read())
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)
