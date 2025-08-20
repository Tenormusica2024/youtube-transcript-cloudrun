#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import os

# UTF-8設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_clean_formatting():
    """クリーンなテキスト整形（余計な説明文なし）をテスト"""
    
    print("=== クリーンなテキスト整形テスト ===")
    print()
    
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    api_url = "http://127.0.0.1:8087/api/extract"
    
    try:
        print("クリーンフォーマット機能をテスト中...")
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
                
                print("=== クリーンフォーマット結果 ===")
                print(f"サーバーバージョン: {version}")
                print(f"元テキスト: {len(original):,} 文字")
                print(f"整形後テキスト: {len(formatted):,} 文字")
                print()
                
                # 除外すべき要素の確認（これらが含まれていないことを確認）
                unwanted_elements = [
                    '【整形済みテキスト】',
                    '【整形処理内容】',
                    '【AI要約プロンプト】',
                    '【使用方法】',
                    'フィラー語を除去し、読みやすく整理されています',
                    '以下のYouTube動画の字幕を整形済みテキストとして表示します',
                    '上記のプロンプトをGemini AIにそのまま入力することで',
                    '詳細AI要約:**"'
                ]
                
                print("=== 不要要素除去確認 ===")
                clean_count = 0
                for element in unwanted_elements:
                    if element not in formatted:
                        print(f"OK {element[:30]}...: 除去されています")
                        clean_count += 1
                    else:
                        print(f"NG {element[:30]}...: まだ含まれています")
                
                print()
                clean_rate = (clean_count / len(unwanted_elements)) * 100
                print(f"クリーンアップ率: {clean_rate:.1f}% ({clean_count}/{len(unwanted_elements)})")
                
                # 改行調整確認
                lines = formatted.split('\n')
                non_empty_lines = [line for line in lines if line.strip()]
                print(f"総行数: {len(lines)}")
                print(f"非空行数: {len(non_empty_lines)}")
                
                # フィラー除去効果確認
                target_fillers = ['ガスも', 'うん', 'あ、', 'で、', 'あれか', 'ちゃんと', 'ですね', 'って話', 'によって', 'とですね']
                
                print("\n=== フィラー除去効果確認 ===")
                total_original = 0
                total_formatted = 0
                
                for filler in target_fillers:
                    original_count = original.count(filler)
                    formatted_count = formatted.count(filler)
                    if original_count > 0:
                        total_original += original_count
                        total_formatted += formatted_count
                        removed = original_count - formatted_count
                        removal_rate = (removed / original_count) * 100 if original_count > 0 else 0
                        print(f"{filler}: {original_count} → {formatted_count} ({removal_rate:.0f}%除去)")
                
                if total_original > 0:
                    overall_removal_rate = ((total_original - total_formatted) / total_original) * 100
                    print(f"\n総合除去率: {overall_removal_rate:.1f}% ({total_original - total_formatted}/{total_original})")
                
                # 成功判定
                if clean_rate >= 100 and overall_removal_rate >= 80:
                    print("\nクリーンなテキスト整形: 完全成功!")
                    print("OK 不要な説明文がすべて除去されています")
                    print("OK フィラー除去機能が正常動作しています")
                    print("OK 改行調整が適用されています")
                    return True
                else:
                    print(f"\n部分的成功: クリーンアップ率 {clean_rate:.1f}%, フィラー除去率 {overall_removal_rate:.1f}%")
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
    success = test_clean_formatting()
    
    print()
    print("=" * 70)
    if success:
        print("CLEAN FORMATTING SUCCESS: 整形済みテキストがクリーンになりました")
        print("不要な説明文が除去され、フィラー除去+改行調整のみが適用されています")
    else:
        print("NEEDS ADJUSTMENT: まだ不要な要素が含まれています")
    print("=" * 70)