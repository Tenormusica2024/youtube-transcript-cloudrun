#!/usr/bin/env python3
"""
YouTube Transcript App with ngrok Fixed URL
v1.5.1-clean - Production Ready

CRITICAL: NO DEMO DATA - Production Only
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path


class NgrokManager:
    def __init__(self):
        self.ngrok_process = None
        self.flask_process = None
        self.project_dir = Path(__file__).parent
        self.ngrok_path = "C:\\Users\\Tenormusica\\ngrok.exe"
        self.config_path = self.project_dir / "ngrok_config.yml"

    def setup_environment(self):
        """Setup environment variables for production"""
        os.environ["FLASK_ENV"] = "production"
        os.environ["FLASK_DEBUG"] = "False"
        os.environ["PORT"] = "8085"
        print("✅ Environment configured for production")

    def start_ngrok(self):
        """Start ngrok with fixed domain"""
        print(f"🔧 Starting ngrok with config: {self.config_path}")

        try:
            self.ngrok_process = subprocess.Popen(
                [
                    self.ngrok_path,
                    "start",
                    "--config",
                    str(self.config_path),
                    "yt-transcript",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print("⏳ Waiting for ngrok tunnel to establish...")
            time.sleep(3)

            if self.ngrok_process.poll() is None:
                print("✅ ngrok tunnel established successfully")
                print("🌐 Fixed URL: https://yt-transcript.ngrok.io")
                return True
            else:
                stdout, stderr = self.ngrok_process.communicate()
                print(f"❌ ngrok failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False

        except Exception as e:
            print(f"❌ Error starting ngrok: {e}")
            return False

    def start_flask_app(self):
        """Start Flask application"""
        print("🚀 Starting Flask application...")

        try:
            self.flask_process = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            print("✅ Flask application started on port 8085")
            return True

        except Exception as e:
            print(f"❌ Error starting Flask app: {e}")
            return False

    def monitor_processes(self):
        """Monitor both processes"""
        print("👀 Monitoring processes...")

        while True:
            try:
                # Check ngrok process
                if self.ngrok_process and self.ngrok_process.poll() is not None:
                    print("⚠️ ngrok process died, restarting...")
                    self.start_ngrok()

                # Check Flask process
                if self.flask_process and self.flask_process.poll() is not None:
                    print("⚠️ Flask process died, restarting...")
                    self.start_flask_app()

                time.sleep(10)

            except KeyboardInterrupt:
                print("\n🛑 Shutdown requested...")
                self.cleanup()
                break

    def cleanup(self):
        """Clean shutdown of all processes"""
        print("🧹 Cleaning up processes...")

        if self.ngrok_process:
            self.ngrok_process.terminate()
            print("✅ ngrok process terminated")

        if self.flask_process:
            self.flask_process.terminate()
            print("✅ Flask process terminated")

    def run(self):
        """Main execution flow"""
        print("=" * 60)
        print("🎯 YouTube Transcript App - ngrok固定URL版 v1.5.1-clean")
        print("🚫 DEMO DATA REMOVED - Production Only")
        print("=" * 60)

        # Setup signal handlers
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup())
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup())

        # Setup environment
        self.setup_environment()

        # Start Flask app first
        if not self.start_flask_app():
            print("❌ Failed to start Flask app")
            return False

        # Wait for Flask to initialize
        time.sleep(2)

        # Start ngrok tunnel
        if not self.start_ngrok():
            print("❌ Failed to start ngrok tunnel")
            self.cleanup()
            return False

        print("\n" + "=" * 60)
        print("🎉 SYSTEM READY!")
        print("🌐 Public URL: https://yt-transcript.ngrok.io")
        print("🏠 Local URL: http://127.0.0.1:8085")
        print("=" * 60)
        print("Press Ctrl+C to stop all services")
        print("=" * 60 + "\n")

        # Monitor processes
        self.monitor_processes()

        return True


if __name__ == "__main__":
    manager = NgrokManager()
    success = manager.run()
    sys.exit(0 if success else 1)
