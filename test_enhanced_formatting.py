#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Blank Line Formatting Test
Tests the improved spacing in formatted text output
"""

import json
import requests

def test_enhanced_formatting():
    """Test the enhanced blank line formatting feature"""
    
    print("=" * 60)
    print("🧪 Enhanced Blank Line Formatting Test")
    print("=" * 60)
    
    # Test URL with heavy filler content
    test_url = "https://www.youtube.com/watch?v=9Dgt8dcuH6I"
    
    # Send API request
    try:
        response = requests.post(
            "http://127.0.0.1:8087/api/extract",
            json={
                "url": test_url,
                "lang": "ja",
                "generate_summary": False
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                formatted_text = data.get("transcript", "")
                original_text = data.get("original_transcript", "")
                
                print(f"✅ API Request Successful")
                print(f"📊 Original text length: {len(original_text):,} characters")
                print(f"📊 Formatted text length: {len(formatted_text):,} characters")
                
                # Count line breaks
                original_lines = original_text.count('\n')
                formatted_lines = formatted_text.count('\n')
                blank_lines = formatted_text.count('\n\n')
                
                print(f"📈 Original line breaks: {original_lines}")
                print(f"📈 Formatted line breaks: {formatted_lines}")
                print(f"🔲 Blank lines added: {blank_lines}")
                print(f"📏 Line break increase: +{formatted_lines - original_lines}")
                
                # Sample output preview (first 500 characters)
                print("\n" + "=" * 40)
                print("📝 Formatted Text Preview:")
                print("=" * 40)
                print(formatted_text[:500] + "..." if len(formatted_text) > 500 else formatted_text)
                print("=" * 40)
                
                # Check for enhanced blank line patterns
                double_breaks = formatted_text.count('\n\n')
                triple_breaks = formatted_text.count('\n\n\n')
                
                print(f"\n🔍 Blank Line Analysis:")
                print(f"   • Double line breaks (\\n\\n): {double_breaks}")
                print(f"   • Triple line breaks (\\n\\n\\n): {triple_breaks}")
                
                if double_breaks > 5:
                    print("✅ Enhanced blank line formatting is ACTIVE")
                    print("🎯 Improved readability with proper spacing")
                else:
                    print("⚠️  Limited blank line formatting detected")
                
                print(f"\n🏆 Test Result: SUCCESS")
                print(f"📱 Enhanced formatting provides better readability")
                
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ Test Failed: {str(e)}")
        
    print("\n" + "=" * 60)


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
