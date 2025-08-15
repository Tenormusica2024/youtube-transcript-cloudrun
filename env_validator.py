#!/usr/bin/env python3
"""
環境変数検証ツール - YouTube Transcript Extractor
全ての必要な環境変数が正しく設定されているかを確認し、不足があれば自動修正を提案
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 必要な環境変数の定義
REQUIRED_ENV_VARS = {
    # APIキー類
    "YOUTUBE_API_KEY": {
        "description": "YouTube Data API v3のAPIキー",
        "required": True,
        "default": None,
        "validation": lambda x: len(x) == 39 and x.startswith("AIza"),
        "error_msg": "YouTube APIキーが無効です（39文字、'AIza'で開始する必要があります）"
    },
    "GEMINI_API_KEY": {
        "description": "Google Gemini AIのAPIキー", 
        "required": True,
        "default": None,
        "validation": lambda x: len(x) == 39 and x.startswith("AIza"),
        "error_msg": "Gemini APIキーが無効です（39文字、'AIza'で開始する必要があります）"
    },
    "TRANSCRIPT_API_TOKEN": {
        "description": "/extractエンドポイント認証用トークン",
        "required": True,
        "default": "hybrid-yt-token-2024",
        "validation": lambda x: len(x) >= 8,
        "error_msg": "認証トークンは8文字以上である必要があります"
    },
    "API_AUTH_TOKEN": {
        "description": "レガシー認証トークン（互換性維持用）",
        "required": False,
        "default": "hybrid-yt-token-2024",
        "validation": lambda x: len(x) >= 8,
        "error_msg": "認証トークンは8文字以上である必要があります"
    },
    
    # 設定値
    "PORT": {
        "description": "サーバーポート番号",
        "required": False,
        "default": "8765",
        "validation": lambda x: x.isdigit() and 1024 <= int(x) <= 65535,
        "error_msg": "ポート番号は1024-65535の範囲で数値である必要があります"
    },
    "MAX_TRANSCRIPT_LENGTH": {
        "description": "字幕最大文字数制限",
        "required": False,
        "default": "50000",
        "validation": lambda x: x.isdigit() and int(x) > 1000,
        "error_msg": "字幕最大長は1000文字以上の数値である必要があります"
    },
    "PYTHONIOENCODING": {
        "description": "Python文字エンコーディング",
        "required": False,
        "default": "utf-8",
        "validation": lambda x: x.lower() in ["utf-8", "utf8"],
        "error_msg": "文字エンコーディングはutf-8である必要があります"
    },
    
    # CORS設定
    "ALLOWED_ORIGINS": {
        "description": "CORS許可オリジン",
        "required": False,
        "default": "https://www.youtube.com,https://m.youtube.com,https://music.youtube.com",
        "validation": lambda x: all(origin.strip().startswith(("http://", "https://")) for origin in x.split(",")),
        "error_msg": "全てのオリジンはhttp://またはhttps://で開始する必要があります"
    }
}

class EnvValidator:
    """環境変数バリデーター"""
    
    def __init__(self, env_file_path=".env"):
        self.env_file = Path(env_file_path)
        self.issues = []
        self.warnings = []
        self.fixes = []
        
        # .envファイルを読み込み
        if self.env_file.exists():
            load_dotenv(self.env_file)
        else:
            self.issues.append(f"⚠️  .envファイルが見つかりません: {self.env_file.absolute()}")
    
    def validate_all(self):
        """全ての環境変数を検証"""
        print(f"🔍 環境変数検証開始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 .envファイル: {self.env_file.absolute()}")
        print("=" * 70)
        
        for var_name, config in REQUIRED_ENV_VARS.items():
            self._validate_single_var(var_name, config)
        
        self._print_summary()
        return len(self.issues) == 0
    
    def _validate_single_var(self, var_name, config):
        """単一の環境変数を検証"""
        current_value = os.getenv(var_name)
        
        # 必須変数のチェック
        if config["required"] and not current_value:
            if config["default"]:
                self.issues.append(f"❌ {var_name}: 必須環境変数が未設定")
                self.fixes.append(f"   → 推奨値: {var_name}={config['default']}")
            else:
                self.issues.append(f"❌ {var_name}: 必須環境変数が未設定（デフォルト値なし）")
            return
        
        # オプション変数でデフォルト値設定
        if not current_value and config["default"]:
            self.warnings.append(f"⚠️  {var_name}: 未設定（デフォルト値使用）")
            self.fixes.append(f"   → 推奨設定: {var_name}={config['default']}")
            return
        
        # 値の妥当性チェック
        if current_value and config["validation"]:
            try:
                if not config["validation"](current_value):
                    self.issues.append(f"❌ {var_name}: {config['error_msg']}")
                    self.issues.append(f"   現在値: {current_value[:20]}..." if len(current_value) > 20 else f"   現在値: {current_value}")
                else:
                    print(f"✅ {var_name}: OK")
            except Exception as e:
                self.issues.append(f"❌ {var_name}: 検証エラー - {e}")
    
    def _print_summary(self):
        """検証結果サマリーを表示"""
        print("\n" + "=" * 70)
        print("📊 検証結果サマリー")
        print("=" * 70)
        
        if self.issues:
            print(f"❌ エラー数: {len(self.issues)}")
            for issue in self.issues:
                print(f"   {issue}")
        
        if self.warnings:
            print(f"\n⚠️  警告数: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"   {warning}")
        
        if self.fixes:
            print(f"\n🔧 推奨修正:")
            for fix in self.fixes:
                print(f"   {fix}")
        
        if not self.issues and not self.warnings:
            print("✅ 全ての環境変数が正しく設定されています！")
        
        print("=" * 70)
    
    def auto_fix_env_file(self):
        """環境変数を自動修正"""
        if not self.fixes:
            print("🎯 修正が必要な項目はありません。")
            return
        
        print(f"🔧 .envファイルの自動修正を開始...")
        
        # 現在の.envファイルの内容を読み込み
        existing_content = ""
        existing_vars = set()
        
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
                for line in existing_content.split('\n'):
                    if '=' in line and not line.strip().startswith('#'):
                        var_name = line.split('=')[0].strip()
                        existing_vars.add(var_name)
        
        # 不足している環境変数を追加
        additions = []
        for var_name, config in REQUIRED_ENV_VARS.items():
            if var_name not in existing_vars and config["default"]:
                additions.append(f"\n# {config['description']}")
                additions.append(f"{var_name}={config['default']}")
        
        if additions:
            backup_file = f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # バックアップ作成
            if self.env_file.exists():
                import shutil
                shutil.copy2(self.env_file, backup_file)
                print(f"📋 バックアップ作成: {backup_file}")
            
            # 新しい内容を書き込み
            with open(self.env_file, 'a', encoding='utf-8') as f:
                f.write(f"\n\n# Auto-generated by env_validator.py - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                for addition in additions:
                    f.write(f"\n{addition}")
            
            print(f"✅ {len(additions)//2}個の環境変数を追加しました。")
            print("🔄 変更を反映するためにサービスを再起動してください。")
        else:
            print("ℹ️  追加すべき環境変数はありません。")

def main():
    """メイン実行関数"""
    print("🎯 YouTube Transcript Extractor - 環境変数検証ツール")
    print("=" * 70)
    
    validator = EnvValidator()
    
    # 検証実行
    is_valid = validator.validate_all()
    
    if not is_valid:
        print("\n🤔 自動修正を実行しますか？ (y/N): ", end="")
        response = input().strip().lower()
        
        if response in ['y', 'yes']:
            validator.auto_fix_env_file()
            print("\n🔄 再検証を実行中...")
            validator_recheck = EnvValidator()
            validator_recheck.validate_all()
        else:
            print("ℹ️  手動で修正してください。")
    
    return 0 if is_valid else 1

if __name__ == "__main__":
    sys.exit(main())