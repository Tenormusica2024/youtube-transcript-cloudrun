#!/usr/bin/env python3
"""
YouTube Transcript App - ngrok Dynamic URL Version
v1.5.1-clean - Production Ready (NO DEMO DATA)

動的URL版 - デモ版データ完全削除済み
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests


class NgrokDynamicManager:
    def __init__(self):
        self.ngrok_process = None
        self.project_dir = Path(__file__).parent
        self.ngrok_path = "C:\\Users\\Tenormusica\\ngrok.exe"

    def start_ngrok_tunnel(self):
        """Start ngrok tunnel with dynamic URL"""
        print("🔧 Starting ngrok tunnel (dynamic URL)...")

        try:
            # Start ngrok in background
            self.ngrok_process = subprocess.Popen(
                [self.ngrok_path, "http", "8085", "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print("⏳ Waiting for ngrok tunnel to establish...")
            time.sleep(5)

            # Get tunnel URL from ngrok API
            tunnel_url = self.get_tunnel_url()
            if tunnel_url:
                print(f"✅ ngrok tunnel established successfully!")
                print(f"🌐 Public URL: {tunnel_url}")
                return tunnel_url
            else:
                print("❌ Failed to get tunnel URL")
                return None

        except Exception as e:
            print(f"❌ Error starting ngrok: {e}")
            return None

    def get_tunnel_url(self, max_retries=10):
        """Get public URL from ngrok local API"""
        for i in range(max_retries):
            try:
                response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    tunnels = data.get("tunnels", [])

                    for tunnel in tunnels:
                        if tunnel.get("proto") == "https":
                            return tunnel.get("public_url")

                    # If no HTTPS, get HTTP and convert
                    for tunnel in tunnels:
                        if tunnel.get("proto") == "http":
                            http_url = tunnel.get("public_url")
                            return http_url.replace("http://", "https://")

            except requests.exceptions.RequestException:
                pass

            print(f"⏳ Retry {i+1}/{max_retries}: Getting tunnel URL...")
            time.sleep(2)

        return None

    def create_access_info(self, tunnel_url):
        """Create access information file"""
        info = {
            "status": "active",
            "version": "v1.5.1-clean",
            "public_url": tunnel_url,
            "local_url": "http://127.0.0.1:8085",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "demo_data_removed": True,
            "production_ready": True,
        }

        with open(
            self.project_dir / "ngrok_access_info.json", "w", encoding="utf-8"
        ) as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        print(f"📝 Access info saved to: ngrok_access_info.json")

    def run(self):
        """Main execution"""
        print("=" * 70)
        print("🎯 YouTube Transcript App - ngrok Dynamic URL版 v1.5.1-clean")
        print("🚫 DEMO DATA COMPLETELY REMOVED - Production Only")
        print("=" * 70)

        # Check if Flask app is running
        print("🔍 Checking Flask application status...")
        try:
            response = requests.get("http://127.0.0.1:8085", timeout=5)
            if response.status_code == 200:
                print("✅ Flask app is running on port 8085")
            else:
                print("⚠️ Flask app responded with non-200 status")
        except requests.exceptions.RequestException:
            print("❌ Flask app is not running on port 8085")
            print("💡 Please start Flask app first: python app.py")
            return False

        # Start ngrok tunnel
        tunnel_url = self.start_ngrok_tunnel()
        if not tunnel_url:
            print("❌ Failed to establish ngrok tunnel")
            return False

        # Create access info
        self.create_access_info(tunnel_url)

        print("\n" + "=" * 70)
        print("🎉 SYSTEM READY!")
        print(f"🌐 Public URL: {tunnel_url}")
        print("🏠 Local URL: http://127.0.0.1:8085")
        print("📝 Access info: ngrok_access_info.json")
        print("=" * 70)
        print("Press Ctrl+C to stop ngrok tunnel")
        print("=" * 70 + "\n")

        # Keep running until interrupted
        try:
            while True:
                if self.ngrok_process.poll() is not None:
                    print("⚠️ ngrok process died")
                    break
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
        finally:
            if self.ngrok_process:
                self.ngrok_process.terminate()
                print("✅ ngrok process terminated")

        return True


if __name__ == "__main__":
    manager = NgrokDynamicManager()
    success = manager.run()
    sys.exit(0 if success else 1)
