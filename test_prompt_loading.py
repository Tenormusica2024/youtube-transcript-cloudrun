"""
プロンプトファイル読み込み機能のテストスクリプト
"""
import sys
import os

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(__file__))

from app import load_prompt_from_file

def test_prompt_loading():
    """プロンプトファイル読み込み機能をテスト"""
    
    # テスト用のサンプルテキスト
    sample_text = "これはテスト用の字幕テキストです。複数の文があります。内容を確認します。"
    
    print("プロンプトファイル読み込みテスト開始")
    
    # 整形プロンプトテスト
    print("\n整形プロンプトテスト:")
    format_prompt = load_prompt_from_file("format_prompt.txt", sample_text)
    if format_prompt:
        print("SUCCESS: format_prompt.txt 読み込み成功")
        print(f"プロンプト長: {len(format_prompt)} 文字")
        print("プロンプトの最初の100文字:")
        print(f"   {format_prompt[:100]}...")
    else:
        print("ERROR: format_prompt.txt 読み込み失敗")
    
    # 要約プロンプトテスト
    print("\n要約プロンプトテスト:")
    summary_prompt = load_prompt_from_file("summary_prompt.txt", sample_text)
    if summary_prompt:
        print("SUCCESS: summary_prompt.txt 読み込み成功")
        print(f"プロンプト長: {len(summary_prompt)} 文字")
        print("プロンプトの最初の100文字:")
        print(f"   {summary_prompt[:100]}...")
    else:
        print("ERROR: summary_prompt.txt 読み込み失敗")
    
    # 存在しないファイルのテスト
    print("\n存在しないファイルのテスト:")
    nonexistent_prompt = load_prompt_from_file("nonexistent.txt", sample_text)
    if nonexistent_prompt is None:
        print("SUCCESS: 存在しないファイルは正常にNoneを返す")
    else:
        print("ERROR: 存在しないファイルのハンドリングが不正")
    
    print("\nテスト完了")

if __name__ == "__main__":
    test_prompt_loading()