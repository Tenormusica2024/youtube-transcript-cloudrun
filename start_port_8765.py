#!/usr/bin/env python3
"""
YouTube要約アプリを専用ポート8765で起動するスクリプト
他のプロジェクトとの干渉を回避
"""

import os
import sys

# ポートを強制的に8765に設定
os.environ["PORT"] = "8765"

# appモジュールをインポートして起動
if __name__ == "__main__":
    # appモジュールをリロードして設定を反映
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # 直接起動処理を実行
    import app

    # 強制的にポート番号を更新
    app.PORT = 8765

    print(f"YouTube Transcript App starting on port {app.PORT}")
    print(f"Access URL: http://localhost:{app.PORT}/")

    # ローカル開発環境として起動
    app.app.run(host="127.0.0.1", port=8765, debug=True)
