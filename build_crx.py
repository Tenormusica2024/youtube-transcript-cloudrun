#!/usr/bin/env python3
"""
YouTube Transcript Extractor - CRX Package Builder
Chrome拡張機能のCRXファイル自動生成スクリプト
"""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


class CRXBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.extension_dir = self.project_root / "chrome-extension"
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"

    def setup_directories(self):
        """ビルド用ディレクトリ作成"""
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        print(f"ビルドディレクトリ準備完了: {self.build_dir}")

    def validate_extension(self):
        """拡張機能の妥当性チェック"""
        print("拡張機能の妥当性をチェック中...")

        # manifest.json確認
        manifest_path = self.extension_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError("manifest.json が見つかりません")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # 必須フィールドチェック
        required_fields = ["manifest_version", "name", "version"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"manifest.json に {field} が不足しています")

        # アイコンファイルチェック
        icons_dir = self.extension_dir / "icons"
        required_icons = ["icon-16.png", "icon-32.png", "icon-48.png", "icon-128.png"]

        for icon in required_icons:
            icon_path = icons_dir / icon
            if not icon_path.exists():
                print(f"警告: {icon} が見つかりません")

        print(f"OK 拡張機能検証完了: {manifest['name']} v{manifest['version']}")
        return manifest

    def create_zip_package(self, manifest):
        """ZIPパッケージ作成"""
        version = manifest["version"]
        zip_filename = f"youtube-transcript-extractor-v{version}.zip"
        zip_path = self.dist_dir / zip_filename

        print(f"ZIPパッケージ作成中: {zip_filename}")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 拡張機能ディレクトリ内の全ファイルを追加
            for file_path in self.extension_dir.rglob("*"):
                if file_path.is_file():
                    # 相対パスを計算
                    arc_name = file_path.relative_to(self.extension_dir)
                    zipf.write(file_path, arc_name)
                    print(f"  追加: {arc_name}")

        file_size = zip_path.stat().st_size
        print(f"OK ZIPパッケージ作成完了: {zip_path} ({file_size:,} bytes)")
        return zip_path

    def create_crx_package(self, manifest):
        """CRXパッケージ作成（簡易版）"""
        version = manifest["version"]
        crx_filename = f"youtube-transcript-extractor-v{version}.crx"

        print("CRXパッケージ作成中...")
        print("注意: 実際のCRXファイルには署名が必要です")
        print("現在はZIP形式で.crxファイルを作成しています")

        # 一時的にZIPをCRXとしてコピー
        zip_path = self.dist_dir / f"youtube-transcript-extractor-v{version}.zip"
        crx_path = self.dist_dir / crx_filename

        if zip_path.exists():
            shutil.copy2(zip_path, crx_path)
            print(f"OK CRXパッケージ作成完了: {crx_path}")
            return crx_path
        else:
            print("NG CRXパッケージ作成失敗: ZIPファイルが見つかりません")
            return None

    def create_userscript_package(self):
        """Tampermonkeyユーザースクリプトパッケージ"""
        userscript_src = self.project_root / "tampermonkey-userscript.js"
        userscript_dst = self.dist_dir / "youtube-transcript-extractor.user.js"

        if userscript_src.exists():
            shutil.copy2(userscript_src, userscript_dst)
            print(f"OK ユーザースクリプト準備完了: {userscript_dst}")
            return userscript_dst
        else:
            print("NG ユーザースクリプトが見つかりません")
            return None

    def create_install_page(self, manifest, packages):
        """インストールページ更新"""
        install_src = self.project_root / "install_instructions.html"
        install_dst = self.dist_dir / "index.html"

        if install_src.exists():
            # インストールページをdistディレクトリにコピー
            shutil.copy2(install_src, install_dst)

            # 相対パスを修正
            with open(install_dst, "r", encoding="utf-8") as f:
                content = f.read()

            # 相対パス修正
            content = content.replace(
                "./tampermonkey-userscript.js", "youtube-transcript-extractor.user.js"
            )
            content = content.replace("./chrome-extension/", "../chrome-extension/")

            with open(install_dst, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"OK インストールページ準備完了: {install_dst}")
            return install_dst
        else:
            print("NG インストールページが見つかりません")
            return None

    def generate_checksums(self):
        """チェックサムファイル生成"""
        import hashlib

        checksums_path = self.dist_dir / "checksums.txt"

        with open(checksums_path, "w", encoding="utf-8") as f:
            f.write("# YouTube Transcript Extractor - File Checksums\n")
            f.write(f"# Generated: {self.get_timestamp()}\n\n")

            for file_path in self.dist_dir.glob("*"):
                if file_path.is_file() and file_path.name != "checksums.txt":
                    # SHA256チェックサム計算
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as f_bytes:
                        for byte_block in iter(lambda: f_bytes.read(4096), b""):
                            sha256_hash.update(byte_block)

                    checksum = sha256_hash.hexdigest()
                    file_size = file_path.stat().st_size

                    f.write(f"{checksum}  {file_path.name} ({file_size:,} bytes)\n")

        print(f"OK チェックサムファイル生成完了: {checksums_path}")

    def get_timestamp(self):
        """現在時刻のタイムスタンプ"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def build_all(self):
        """全パッケージビルド実行"""
        print("=" * 60)
        print("YouTube Transcript Extractor - ビルド開始")
        print("=" * 60)

        try:
            # 1. 準備
            self.setup_directories()

            # 2. 検証
            manifest = self.validate_extension()

            # 3. パッケージ作成
            packages = {}

            # ZIP作成
            packages["zip"] = self.create_zip_package(manifest)

            # CRX作成
            packages["crx"] = self.create_crx_package(manifest)

            # ユーザースクリプト準備
            packages["userscript"] = self.create_userscript_package()

            # インストールページ準備
            packages["install_page"] = self.create_install_page(manifest, packages)

            # 4. チェックサム生成
            self.generate_checksums()

            # 5. 完了レポート
            self.print_build_report(manifest, packages)

        except Exception as e:
            print(f"NG ビルドエラー: {e}")
            return False

        return True

    def print_build_report(self, manifest, packages):
        """ビルド完了レポート"""
        print("\n" + "=" * 60)
        print("OK ビルド完了!")
        print("=" * 60)

        print(f"プロジェクト: {manifest['name']}")
        print(f"バージョン: {manifest['version']}")
        print(f"出力先: {self.dist_dir}")

        print(f"\n生成されたファイル:")
        for file_path in self.dist_dir.glob("*"):
            if file_path.is_file():
                file_size = file_path.stat().st_size
                print(f"  OK {file_path.name} ({file_size:,} bytes)")

        print(f"\n配布準備完了:")
        print(f"  Chrome拡張機能: {packages.get('zip', 'N/A')}")
        print(f"  CRXファイル: {packages.get('crx', 'N/A')}")
        print(f"  Tampermonkey: {packages.get('userscript', 'N/A')}")
        print(f"  インストールページ: {packages.get('install_page', 'N/A')}")

        print(f"\n次のステップ:")
        print(f"  1. GitHub Pages用に dist/ フォルダをプッシュ")
        print(f"  2. Chrome Web Store審査提出（任意）")
        print(f"  3. ユーザーへの配布案内")


if __name__ == "__main__":
    builder = CRXBuilder()
    success = builder.build_all()

    if success:
        print("\nビルドプロセス完了！")
    else:
        print("\nビルドプロセス失敗")
        exit(1)
