#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hashlib
import importlib
import os
import sys


def server_environment_diagnostics():
    """サーバー環境の詳細診断"""

    print("=== サーバー環境診断 ===")
    print()

    # 1. Python環境確認
    print("=== Python環境 ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print()

    # 2. ファイルの存在確認
    print("=== ファイル存在確認 ===")
    files_to_check = [
        "production_server.py",
        "fixed_production_server.py",
        "templates/index.html",
    ]

    for file_path in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)
            print(f"OK {file_path}: {file_size} bytes, modified: {mod_time}")
        else:
            print(f"NG {file_path}: NOT FOUND")
    print()

    # 3. production_server.pyの詳細分析
    print("=== production_server.py 分析 ===")
    try:
        with open("production_server.py", "r", encoding="utf-8") as f:
            content = f.read()

        # ファイルハッシュ
        file_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        print(f"ファイルハッシュ: {file_hash}")

        # 重要な関数の存在確認
        functions_to_check = [
            "format_transcript_text",
            "FILLER REMOVAL START",
            "FILLER REMOVAL COMPLETE",
            "v1.3.12-fixed",
        ]

        for func in functions_to_check:
            if func in content:
                print(f"OK {func}: FOUND")
            else:
                print(f"NG {func}: NOT FOUND")

        # format_transcript_text関数の詳細確認
        if "def format_transcript_text(" in content:
            start_pos = content.find("def format_transcript_text(")
            end_pos = content.find("\ndef ", start_pos + 1)
            if end_pos == -1:
                end_pos = content.find("\nclass ", start_pos + 1)
            if end_pos == -1:
                end_pos = len(content)

            function_content = content[start_pos:end_pos]
            function_lines = len(function_content.split("\n"))
            print(f"format_transcript_text関数: {function_lines} lines")

            # 重要なキーワードの確認
            critical_keywords = [
                "FILLER REMOVAL START",
                "specific_fillers",
                "flush=True",
            ]
            for keyword in critical_keywords:
                if keyword in function_content:
                    print(f"  OK {keyword}: FOUND in function")
                else:
                    print(f"  NG {keyword}: NOT FOUND in function")

    except Exception as e:
        print(f"ファイル分析エラー: {e}")
    print()

    # 4. モジュールのリロード状況確認
    print("=== モジュール状況 ===")
    if "production_server" in sys.modules:
        module = sys.modules["production_server"]
        if hasattr(module, "format_transcript_text"):
            print("OK format_transcript_text: モジュールにロード済み")

            # 関数のソースコード確認
            import inspect

            try:
                source = inspect.getsource(module.format_transcript_text)
                if "FILLER REMOVAL START" in source:
                    print("OK 新しいformat_transcript_text関数がロード済み")
                else:
                    print("NG 古いformat_transcript_text関数がロード中")
            except Exception as e:
                print(f"ソースコード確認エラー: {e}")
        else:
            print("NG format_transcript_text: モジュールに未ロード")
    else:
        print("NG production_server: モジュール未ロード")
    print()

    # 5. キャッシュファイル確認
    print("=== キャッシュファイル確認 ===")
    cache_patterns = ["__pycache__", "*.pyc", "*.pyo"]
    for pattern in cache_patterns:
        if pattern == "__pycache__":
            if os.path.exists(pattern):
                cache_files = os.listdir(pattern)
                print(f"OK {pattern}: {len(cache_files)} files")
                for cache_file in cache_files:
                    if "production_server" in cache_file:
                        cache_path = os.path.join(pattern, cache_file)
                        cache_time = os.path.getmtime(cache_path)
                        print(f"  - {cache_file}: {cache_time}")
            else:
                print(f"NG {pattern}: NOT FOUND")

    print()
    return True


if __name__ == "__main__":
    server_environment_diagnostics()
