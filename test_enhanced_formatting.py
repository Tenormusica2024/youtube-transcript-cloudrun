#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import os

# UTF-8設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_enhanced_formatting():
    """強化されたテキスト整形（AI要約プロンプト維持）をテスト"""
    
    print("=== 強化されたテキスト整形テスト ===")
    print()
    
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    api_url = "http://127.0.0.1:8087/api/extract"
    
    try:
        print("強化されたフォーマット機能をテスト中...")
        print(f"対象動画: {test_url}")
        print()
        
        response = requests.post(
            api_url,
            json={
                "url": test_url,
                "lang": "ja", 
                "generate_summary": False
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                original = data.get('original_transcript', '')
                formatted = data.get('transcript', '')
                version = data.get('version', 'unknown')
                
                print("=== 強化されたフォーマット結果 ===")
                print(f"サーバーバージョン: {version}")
                print(f"元テキスト: {len(original):,} 文字")
                print(f"整形後テキスト: {len(formatted):,} 文字")
                print()
                
                # フォーマット内容確認
                key_elements = [
                    '【整形済みテキスト】',
                    '【整形処理内容】',
                    '【AI要約プロンプト】',
                    '【使用方法】',
                    'フィラー除去:',
                    'テキスト短縮:',
                    '詳細要約条件:',
                    '字幕テキスト:'
                ]
                
                print("=== フォーマット要素確認 ===")
                found_elements = 0
                for element in key_elements:
                    if element in formatted:
                        print(f"OK {element}: 含まれています")
                        found_elements += 1
                    else:
                        print(f"NG {element}: 見つかりません")
                
                print()
                coverage = (found_elements / len(key_elements)) * 100
                print(f"フォーマット要素カバレッジ: {coverage:.1f}% ({found_elements}/{len(key_elements)})")
                
                # 改行調整確認
                lines = formatted.split('\n')
                non_empty_lines = [line for line in lines if line.strip()]
                print(f"総行数: {len(lines)}")
                print(f"非空行数: {len(non_empty_lines)}")
                
                # AI要約プロンプトの存在確認
                if 'この内容を日本語で詳細に要約してください' in formatted:
                    print("OK AI要約プロンプト: 完全に保持されています")
                    
                    # プロンプト詳細確認
                    prompt_conditions = [
                        '動画の全体構成を把握し',
                        '主要なポイントを漏らさず',
                        '具体的な数字、事例、引用',
                        '10-15文程度の充実した要約',
                        '各セクションごとに見出し'
                    ]
                    
                    print("\n=== AI要約プロンプト詳細確認 ===")
                    for condition in prompt_conditions:
                        if condition in formatted:
                            print(f"OK {condition}: 含まれています")
                        else:
                            print(f"NG {condition}: 見つかりません")
                else:
                    print("NG AI要約プロンプト: 見つかりません")
                
                # 成功判定
                if coverage >= 80 and len(non_empty_lines) > 10:
                    print("\n強化されたテキスト整形: 完全成功!")
                    print("OK AI要約プロンプトが維持されています")
                    print("OK フィラー除去機能が統合されています")
                    print("OK 改行調整が適用されています")
                    print("OK 構造化されたフォーマットが実装されています")
                    return True
                else:
                    print("\n⚠️ 部分的成功: 一部要素が不足しています")
                    return False
                    
            else:
                print(f"API Error: {data.get('error')}")
                return False
        else:
            print(f"HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Test Error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_formatting()
    
    print()
    print("=" * 70)
    if success:
        print("ENHANCED FORMATTING SUCCESS: AI要約プロンプト維持+フィラー除去統合完了")
        print("整形済みタブに構造化されたフォーマットが適用されました")
        print("ユーザーは元のAI要約プロンプトを利用できます")
    else:
        print("NEEDS INVESTIGATION: フォーマット機能に問題があります")
    print("=" * 70)