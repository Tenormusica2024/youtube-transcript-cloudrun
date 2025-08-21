#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import sys

import requests

# UTF-8設定
if sys.platform.startswith("win"):
    os.environ["PYTHONIOENCODING"] = "utf-8"


def analyze_actual_fillers():
    """実際のテキストでフィラーの形式を分析"""

    print("=== 実際のフィラー形式分析 ===")
    print()

    # 指定動画からテキスト取得
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    api_url = "http://127.0.0.1:8087/api/extract"

    try:
        response = requests.post(
            api_url,
            json={"url": test_url, "lang": "ja", "generate_summary": False},
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                original_text = data.get("original_transcript", "")

                print("実際のテキストから周辺文脈とともにフィラーを分析:")
                print()

                # フィラー周辺の文脈を抽出
                target_fillers = [
                    "ガスも",
                    "うん",
                    "あ、",
                    "で、",
                    "あれか",
                    "ちゃんと",
                    "ですね",
                    "って話",
                    "によって",
                    "とですね",
                ]

                for filler in target_fillers:
                    # フィラーの前後20文字を取得
                    pattern = rf"(.{{0,20}}){re.escape(filler)}(.{{0,20}})"
                    matches = re.finditer(pattern, original_text, re.DOTALL)

                    match_count = 0
                    for match in matches:
                        match_count += 1
                        if match_count <= 3:  # 最初の3例のみ表示
                            before = match.group(1).replace("\n", " ").strip()
                            after = match.group(2).replace("\n", " ").strip()
                            print(f'{filler}: "...{before}【{filler}】{after}..."')

                    if match_count > 3:
                        print(f"  (他 {match_count-3} 例)")
                    elif match_count == 0:
                        print(f"{filler}: 見つかりませんでした")
                    print()

                print("=== 現在のパターンとの比較分析 ===")
                print()

                # 現在のパターンをテスト
                current_patterns = [
                    ("ガスも", r"ガスも\s*"),
                    ("うん。", r"うん\。\s*"),
                    ("うん", r"うん\s+"),
                    ("あ、", r"あ、\s*"),
                    ("で、", r"で、\s*"),
                    ("あれか、", r"あれか、\s*"),
                    ("あれか", r"あれか\s+"),
                    ("ちゃんと", r"ちゃんと\s+"),
                    ("ですね", r"ですね\s*"),
                    ("って話", r"って話\s*"),
                    ("によって", r"によって\s+"),
                    ("とですね", r"とですね\s*"),
                ]

                for filler_name, pattern in current_patterns:
                    matches = re.findall(pattern, original_text)
                    total_filler_count = original_text.count(filler_name)

                    if total_filler_count > 0:
                        pattern_match_count = len(matches)
                        pattern_effectiveness = (
                            pattern_match_count / total_filler_count
                        ) * 100

                        print(f"{filler_name}:")
                        print(f"  総出現数: {total_filler_count}")
                        print(f"  パターンマッチ数: {pattern_match_count}")
                        print(f"  パターン有効性: {pattern_effectiveness:.1f}%")

                        if pattern_effectiveness < 100:
                            print(f"  → パターン改善が必要")
                        print()

                return original_text

            else:
                print(f"API Error: {data.get('error')}")
                return None
        else:
            print(f"HTTP Error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Analysis failed: {e}")
        return None


if __name__ == "__main__":
    text = analyze_actual_fillers()

    if text:
        print("=" * 60)
        print("フィラーの実形式を確認し、正規表現パターンを最適化する必要があります")
        print("=" * 60)
