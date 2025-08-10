#!/usr/bin/env python3
"""
実際のAPIキーを使用したテスト（オプション）
"""

import os
import sys

def main():
    """APIキーありのテスト"""
    
    # ユーザーからAPIキー取得
    print("YouTube Data API v3 キーでのテスト（オプション）")
    print("=" * 50)
    print("注意：実際のAPIキーを入力する場合のみ実行してください")
    print("テストをスキップする場合は空白のままEnterを押してください")
    
    api_key = input("\nYouTube Data API v3 キーを入力（オプション）: ").strip()
    
    if not api_key:
        print("APIキーテストをスキップしました")
        return True
    
    if api_key in ["PLEASE_SET_YOUR_API_KEY", "your_api_key_here"]:
        print("無効なAPIキーです（プレースホルダー値）")
        return False
    
    # 環境変数に一時的に設定
    os.environ['YOUTUBE_API_KEY'] = api_key
    
    try:
        import requests
        
        print("\nYouTube Data API v3 テスト中...")
        
        # テスト用動画の情報取得
        video_id = "dQw4w9WgXcQ"
        url = f"https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet',
            'id': video_id,
            'key': api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                title = data['items'][0]['snippet']['title']
                print(f"✅ API接続成功！")
                print(f"動画タイトル: {title}")
                
                # アプリでのテスト
                print("\nアプリケーション統合テスト...")
                sys.path.insert(0, '.')
                from app import get_video_title
                
                app_title = get_video_title(video_id)
                print(f"アプリ経由のタイトル: {app_title}")
                
                if title == app_title:
                    print("✅ 統合テスト成功！")
                    return True
                else:
                    print("❌ 統合テスト失敗（タイトル不一致）")
                    return False
            else:
                print("❌ 動画データが見つかりません")
                return False
        
        elif response.status_code == 403:
            print("❌ API認証エラー（APIキーが無効）")
            print(f"エラー詳細: {response.text}")
            return False
        else:
            print(f"❌ APIエラー（ステータス: {response.status_code}）")
            print(f"エラー詳細: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        return False
    
    finally:
        # APIキーを環境変数から削除
        os.environ.pop('YOUTUBE_API_KEY', None)

if __name__ == "__main__":
    success = main()
    print(f"\nテスト結果: {'成功' if success else '失敗'}")
    sys.exit(0 if success else 1)