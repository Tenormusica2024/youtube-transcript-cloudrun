#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
import os

# UTF-8設定
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_individual_patterns():
    """個別フィラーパターンのテスト"""
    print("=== 個別フィラーパターンテスト ===")
    print()
    
    # ユーザーが指摘した具体例
    test_samples = [
        "ガスも 出してくれてるんですが",
        "うん。",
        "あ、で、メイン実行関数も",
        "あれか、ちゃんと",
        "ですね。",
        "って話ですよね。",
        "によって制度があるとですね。"
    ]
    
    # 強化パターン
    filler_patterns = {
        'ガスも': r'ガスも[\u3001\u3002\s]*',
        'うん': r'うん[\u3002\u3001\s]*', 
        'あ、': r'あ、[\u3001\u3002\s]*',
        'で、': r'で、[\u3001\u3002\s]*',
        'あれか': r'あれか[\u3001\u3002\s]*',
        'ちゃんと': r'ちゃんと[\u3001\u3002\s]*',
        'ですね': r'ですね[\u3001\u3002\s]*',
        'って話': r'って話[\u3001\u3002\s]*',
        'によって': r'によって[\u3001\u3002\s]*',
        'とですね': r'とですね[\u3001\u3002\s]*'
    }
    
    for sample in test_samples:
        print(f"元テキスト: \"{sample}\"")
        modified = sample
        
        matches_found = []
        for filler_name, pattern in filler_patterns.items():
            if re.search(pattern, modified):
                matches_found.append(filler_name)
                modified = re.sub(pattern, ' ', modified)
        
        print(f"マッチしたパターン: {matches_found}")
        print(f"処理後: \"{modified.strip()}\"")
        print(f"変化: {'はい' if sample != modified.strip() else 'なし'}")
        print()

def test_full_sentence():
    """実際のユーザー指摘文で完全テスト"""
    print("=== 完全文章テスト ===")
    print()
    
    # ユーザーの指摘例文
    test_text = """ガスも 出してくれてるんですが スライドパターンの Googleスライドがないと 厳しいって話ですよね。うん。あ、で、メイン実行関数もあれか、 ちゃんと ジェミに与えておいて理解してもらうこと によって制度があるとですね。うん。"""
    
    print(f"元テキスト:\n{test_text}")
    print()
    
    # 段階的フィラー除去テスト
    text = test_text
    
    # Step 1: 基本フィラー語除去
    basic_patterns = [
        r'ガスも[\u3001\u3002\s]*',
        r'うん[\u3002\u3001\s]*', 
        r'あ、[\u3001\u3002\s]*',
        r'で、[\u3001\u3002\s]*',
        r'あれか[\u3001\u3002\s]*',
        r'ちゃんと[\u3001\u3002\s]*',
        r'ですね[\u3001\u3002\s]*',
        r'って話[\u3001\u3002\s]*',
        r'によって[\u3001\u3002\s]*',
        r'とですね[\u3001\u3002\s]*'
    ]
    
    for pattern in basic_patterns:
        old_text = text
        text = re.sub(pattern, ' ', text)
        if old_text != text:
            print(f"適用パターン: {pattern}")
            print(f"結果: {text}")
            print()
    
    # Step 2: 追加クリーニング
    text = re.sub(r'\s{2,}', ' ', text)  # 連続スペース整理
    text = re.sub(r'[\u3002\u3001]{2,}', '。', text)  # 連続句読点整理
    text = text.strip()
    
    print(f"最終結果:\n{text}")
    print()
    print(f"文字数変化: {len(test_text)} → {len(text)} ({len(test_text)-len(text)}文字削除)")
    
    # 残存フィラーチェック
    remaining_fillers = []
    check_fillers = ['ガスも', 'うん', 'あ、', 'で、', 'あれか', 'ちゃんと', 'ですね', 'って話', 'によって', 'とですね']
    
    for filler in check_fillers:
        if filler in text:
            remaining_fillers.append(filler)
    
    if remaining_fillers:
        print(f"残存フィラー: {remaining_fillers}")
    else:
        print("フィラー除去: 完了")

if __name__ == "__main__":
    test_individual_patterns()
    test_full_sentence()