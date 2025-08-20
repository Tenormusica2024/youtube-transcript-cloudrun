#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

def main():
    print("YouTube Transcript App - Port 8090 Server")
    print("=" * 50)
    
    # UTF-8設定
    if sys.platform.startswith('win'):
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # ポートを8090に設定
    os.environ["PORT"] = "8090"
    
    print(f"Server starting on: http://localhost:8090")
    print("YouTube API: Initializing...")
    print("Gemini API: Initializing...")
    print("=" * 50)
    
    try:
        # 元のappを実行
        import app
        print("Original app loaded successfully")
        app.app.run(host='0.0.0.0', port=8090, debug=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()