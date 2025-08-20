#!/usr/bin/env python3
"""
ngrokトンネルのURL取得スクリプト
"""

import requests
import json
import time

def get_ngrok_tunnel_url():
    """ngrokトンネルのパブリックURLを取得"""
    try:
        # ngrok APIエンドポイント
        api_url = "http://127.0.0.1:4040/api/tunnels"
        
        print("ngrokトンネル情報を取得中...")
        response = requests.get(api_url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            if tunnels:
                for tunnel in tunnels:
                    protocol = tunnel.get('proto', '')
                    public_url = tunnel.get('public_url', '')
                    config = tunnel.get('config', {})
                    local_addr = config.get('addr', '')
                    
                    print(f"トンネル発見:")
                    print(f"  プロトコル: {protocol}")
                    print(f"  パブリックURL: {public_url}")
                    print(f"  ローカルアドレス: {local_addr}")
                    print("-" * 50)
                    
                    # HTTPSトンネルを優先して返す
                    if protocol == 'https' and 'localhost:5001' in local_addr:
                        return public_url
                    elif protocol == 'http' and 'localhost:5001' in local_addr:
                        return public_url
                
                # 最初のトンネルを返す
                return tunnels[0].get('public_url', '')
            else:
                print("アクティブなトンネルが見つかりません")
                return None
        else:
            print(f"ngrok APIエラー: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"接続エラー: {e}")
        return None
    except Exception as e:
        print(f"予期しないエラー: {e}")
        return None

def wait_for_ngrok_ready(max_wait=30):
    """ngrokの準備完了を待機"""
    print("ngrokの準備完了を待機中...")
    
    for i in range(max_wait):
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                if data.get('tunnels'):
                    print("ngrok準備完了!")
                    return True
        except:
            pass
        
        print(f"待機中... ({i+1}/{max_wait})")
        time.sleep(1)
    
    print("ngrokの準備がタイムアウトしました")
    return False

if __name__ == "__main__":
    print("=== ngrokトンネルURL取得ツール ===")
    
    # ngrokの準備完了を待機
    if wait_for_ngrok_ready():
        # トンネルURL取得
        tunnel_url = get_ngrok_tunnel_url()
        
        if tunnel_url:
            print(f"\n🌐 スマホアクセス用URL:")
            print(f"   {tunnel_url}")
            print(f"\n📱 スマホからこのURLにアクセスしてください!")
            print(f"   YouTube字幕抽出アプリが利用できます。")
        else:
            print("\n❌ トンネルURLの取得に失敗しました")
            print("   ngrokが正常に起動していることを確認してください")
    else:
        print("\n❌ ngrokが準備できていません")
        print("   ngrokを再起動してから再試行してください")