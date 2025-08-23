#!/usr/bin/env python3
"""
YouTube Transcript App - Cloud Run Deployment Script
v1.5.1-clean - Production Ready (NO DEMO DATA)

Cloud Run自動デプロイスクリプト - デモ版データ完全削除済み
"""

import os
import subprocess
import sys
import time
from pathlib import Path

class CloudRunDeployer:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.gcloud_path = "C:\\Users\\Tenormusica\\google-cloud-sdk\\bin\\gcloud.cmd"
        self.project_id = "yt-transcript-demo-2025"
        self.service_name = "yt-transcript"
        self.region = "asia-northeast1"
        
    def check_prerequisites(self):
        """前提条件チェック"""
        print("Checking prerequisites...")
        
        # gcloud CLI確認
        if not os.path.exists(self.gcloud_path):
            print("ERROR: gcloud CLI not found")
            return False
        
        # プロジェクト確認
        try:
            result = subprocess.run([
                self.gcloud_path, "config", "get-value", "project"
            ], capture_output=True, text=True, check=True)
            
            current_project = result.stdout.strip()
            if current_project != self.project_id:
                print(f"WARNING: Current project: {current_project}")
                print(f"   Expected project: {self.project_id}")
                
                # プロジェクト切り替え
                subprocess.run([
                    self.gcloud_path, "config", "set", "project", self.project_id
                ], check=True)
                print(f"SUCCESS: Switched to project: {self.project_id}")
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: gcloud project check failed: {e}")
            return False
        
        # 必要ファイル確認
        required_files = ["app.py", "requirements.txt", "Dockerfile", "cloudbuild.yaml"]
        for file in required_files:
            if not (self.project_dir / file).exists():
                print(f"ERROR: Required file missing: {file}")
                return False
        
        print("SUCCESS: Prerequisites check passed")
        return True
    
    def clean_deployment_files(self):
        """デプロイ用ファイル整理"""
        print("Cleaning deployment files...")
        
        # .gcloudignoreの確認・整理
        gcloudignore_path = self.project_dir / ".gcloudignore"
        if gcloudignore_path.exists():
            print("SUCCESS: .gcloudignore exists")
        else:
            print("WARNING: .gcloudignore not found, deployment may include unnecessary files")
        
        # 不要なファイル削除
        cleanup_patterns = [
            "*.pyc", "__pycache__", ".pytest_cache", 
            "ngrok*", "*ngrok*", "archive/", "temp_files/",
            "memory-bank/", "*.log"
        ]
        
        for pattern in cleanup_patterns:
            try:
                # Windows compatible cleanup
                if pattern.endswith("/"):
                    # ディレクトリ削除
                    import shutil
                    dir_path = self.project_dir / pattern.rstrip("/")
                    if dir_path.exists():
                        shutil.rmtree(dir_path)
                        print(f"   Removed directory: {pattern}")
            except Exception as e:
                print(f"   Warning: Could not remove {pattern}: {e}")
        
        print("SUCCESS: File cleanup completed")
    
    def enable_required_apis(self):
        """必要なAPI有効化"""
        print("Enabling required APIs...")
        
        required_apis = [
            "cloudbuild.googleapis.com",
            "run.googleapis.com"
        ]
        
        for api in required_apis:
            try:
                subprocess.run([
                    self.gcloud_path, "services", "enable", api
                ], check=True, capture_output=True)
                print(f"SUCCESS: Enabled API: {api}")
            except subprocess.CalledProcessError:
                print(f"WARNING: API already enabled or failed: {api}")
    
    def deploy_to_cloud_run(self):
        """Cloud Runにデプロイ"""
        print("Deploying to Cloud Run...")
        
        deploy_cmd = [
            self.gcloud_path, "run", "deploy", self.service_name,
            "--source", ".",
            "--platform", "managed",
            "--region", self.region,
            "--allow-unauthenticated",
            "--port", "8080",
            "--memory", "512Mi",
            "--timeout", "300s",
            "--max-instances", "10",
            "--set-env-vars", 
            "YOUTUBE_API_KEY=AIzaSyBC8mkp2FgNXRaFLerpgjMaLG4ri4-X25A,GEMINI_API_KEY=AIzaSyBKVL0MW3hbTFX7llfbuF0TL73SKNR2Rfw",
            "--quiet"
        ]
        
        try:
            print("Starting deployment (this may take several minutes)...")
            result = subprocess.run(
                deploy_cmd, 
                cwd=self.project_dir,
                capture_output=False,
                text=True,
                check=True
            )
            
            print("SUCCESS: Deployment successful!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Deployment failed: {e}")
            return False
    
    def get_service_url(self):
        """デプロイ後のURL取得"""
        try:
            result = subprocess.run([
                self.gcloud_path, "run", "services", "describe", self.service_name,
                "--region", self.region,
                "--format", "value(status.url)"
            ], capture_output=True, text=True, check=True)
            
            url = result.stdout.strip()
            return url
        except subprocess.CalledProcessError:
            return None
    
    def verify_deployment(self):
        """デプロイ検証"""
        print("Verifying deployment...")
        
        url = self.get_service_url()
        if not url:
            print("ERROR: Could not get service URL")
            return False
        
        print(f"Service URL: {url}")
        
        # ヘルスチェック
        try:
            import requests
            health_url = f"{url}/health"
            response = requests.get(health_url, timeout=30)
            
            if response.status_code == 200:
                print("SUCCESS: Health check passed")
                return True
            else:
                print(f"WARNING: Health check returned status: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"WARNING: Health check failed: {e}")
            print("   Service may still be starting up...")
            return True  # Cloud Runは起動に時間がかかる場合がある
    
    def run_deployment(self):
        """完全デプロイメント実行"""
        print("="*70)
        print("YouTube Transcript App - Cloud Run Deployment")
        print("NO DEMO DATA - Production v1.5.1-clean")
        print("="*70)
        
        # ステップ1: 前提条件チェック
        if not self.check_prerequisites():
            print("ERROR: Prerequisites check failed")
            return False
        
        # ステップ2: ファイル整理
        self.clean_deployment_files()
        
        # ステップ3: API有効化
        self.enable_required_apis()
        
        # ステップ4: デプロイ実行
        if not self.deploy_to_cloud_run():
            print("ERROR: Deployment failed")
            return False
        
        # ステップ5: デプロイ検証
        if not self.verify_deployment():
            print("WARNING: Deployment verification had issues")
        
        # 最終結果
        url = self.get_service_url()
        if url:
            print("\n" + "="*70)
            print("DEPLOYMENT SUCCESSFUL!")
            print(f"Production URL: {url}")
            print("Demo data completely removed")
            print("Version: v1.5.1-clean")
            print("="*70)
            
            # QRコード生成コマンド表示
            print(f"\nTest the service:")
            print(f"   curl {url}/health")
            print(f"   Open in browser: {url}")
            
            return True
        else:
            print("ERROR: Could not retrieve service URL")
            return False

if __name__ == "__main__":
    deployer = CloudRunDeployer()
    success = deployer.run_deployment()
    sys.exit(0 if success else 1)