#!/usr/bin/env python3
"""
YouTube字幕抽出ツール - 依存関係自動インストールスクリプト
必要なパッケージを一括インストールします。
"""

import subprocess
import sys
import os

def install_package(package):
    """パッケージをインストール"""
    try:
        print(f"📦 インストール中: {package}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package, "--user"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {package} インストール成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {package} インストール失敗: {e}")
        print(f"エラー出力: {e.stderr}")
        return False

def main():
    """メイン処理"""
    print("YouTube字幕抽出ツール - 依存関係インストール")
    print("=" * 50)
    
    # 必要なパッケージリスト
    packages = [
        "flask",
        "flask-cors", 
        "youtube-transcript-api",
        "qrcode[pil]",
        "python-dotenv",
        "google-generativeai",
        "google-api-python-client",
        "requests",
        "werkzeug"
    ]
    
    success_count = 0
    failed_packages = []
    
    for package in packages:
        if install_package(package):
            success_count += 1
        else:
            failed_packages.append(package)
    
    print("\n" + "=" * 50)
    print("インストール結果:")
    print(f"✅ 成功: {success_count}/{len(packages)}")
    
    if failed_packages:
        print(f"❌ 失敗: {failed_packages}")
        print("\n⚠️  一部パッケージのインストールに失敗しました。")
        print("手動で以下を実行してください:")
        for pkg in failed_packages:
            print(f"   py -3 -m pip install {pkg} --user")
    else:
        print("🎉 全ての依存関係のインストールが完了しました！")
        print("\n次のステップ:")
        print("1. サーバー起動: py -3 app_mobile.py")
        print("2. ブラウザでアクセス: http://127.0.0.1:8085")
    
    return len(failed_packages) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)