import os
import subprocess
import sys

# ポート8085を環境変数に設定
os.environ['PORT'] = '8085'

# app.pyを実行
if __name__ == "__main__":
    subprocess.run([sys.executable, 'app.py'])