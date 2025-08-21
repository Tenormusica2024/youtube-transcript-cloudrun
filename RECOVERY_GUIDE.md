# YouTube Transcript WebApp 復旧ガイド

## 📋 **完全復旧手順書** (v1.3.12-fixed)

### 🎯 **復旧概要**
このガイドでは、YouTube Transcript WebAppを完全に復旧する手順を説明します。

---

## 🔧 **1. システム要件**

### **必要な環境**
- **OS**: Windows 10/11
- **Python**: 3.8以上
- **Git**: インストール済み
- **ポート**: 8087が利用可能

### **必要なAPIキー**
- **Gemini API Key**: `GEMINI_API_KEY` 環境変数
- **YouTube Data API**: 内蔵済み

---

## 📦 **2. 依存関係の確認**

### **コア依存関係**
```
Flask==2.3.3
flask-cors==4.0.0
youtube-transcript-api==1.2.2
google-genai==1.29.0
google-api-python-client==2.100.0
google-auth==2.23.0
python-dotenv==1.0.0
requests==2.31.0
```

### **インストール手順**
```bash
cd C:\Users\Tenormusica\youtube_transcript_webapp
pip install -r requirements.txt
```

---

## 🚀 **3. 復旧手順**

### **Step 1: リポジトリの取得**
```bash
# 新規環境の場合
git clone https://github.com/Tenormusica2024/youtube-transcript-cloudrun.git
cd youtube-transcript-cloudrun

# 既存環境の場合
git pull origin master
```

### **Step 2: 環境変数の設定**
```bash
# .envファイルの作成
echo GEMINI_API_KEY=your_api_key_here > .env
```

### **Step 3: サーバー起動**
```bash
# 方法1: 起動スクリプト使用
start_youtube_transcript_latest.bat

# 方法2: 直接起動
python production_server.py
```

### **Step 4: 動作確認**
- ブラウザで http://127.0.0.1:8087 にアクセス
- テスト動画で機能確認

---

## 🔍 **4. 機能確認チェックリスト**

### **基本機能**
- [ ] YouTube URLからの字幕抽出
- [ ] 日本語・英語字幕対応
- [ ] エラーハンドリング動作

### **高度機能** 
- [ ] フィラー除去機能 (86.9%効果)
- [ ] Gemini AI要約生成
- [ ] クリーンテキスト整形
- [ ] 改行調整機能

### **API確認**
- [ ] POST /api/extract エンドポイント
- [ ] JSON形式のレスポンス
- [ ] エラー時の適切な応答

---

## 📊 **5. トラブルシューティング**

### **よくある問題と解決法**

#### **問題1: サーバーが起動しない**
```bash
# ポート確認
netstat -an | findstr :8087

# プロセス終了
taskkill /F /IM python.exe
```

#### **問題2: フィラー除去が動作しない**
```bash
# Pythonキャッシュクリア
rd /s /q __pycache__
del *.pyc

# サーバー再起動
python production_server.py
```

#### **問題3: Gemini API エラー**
```bash
# 環境変数確認
echo %GEMINI_API_KEY%

# .envファイル確認
type .env
```

---

## 🔄 **6. バックアップ・復元**

### **現在の状態をバックアップ**
```bash
# Gitコミット
git add -A
git commit -m "Current working state backup"
git push origin master
```

### **特定バージョンに復元**
```bash
# 最新の安定版に復元
git checkout 9774aff

# 強制復元（変更を破棄）
git reset --hard 9774aff
```

---

## 📈 **7. パフォーマンス指標**

### **期待値**
- **起動時間**: 10秒以内
- **API応答時間**: 2秒以内（通常の動画）
- **フィラー除去率**: 85%以上
- **メモリ使用量**: 100MB以下

### **監視項目**
- ポート8087の応答
- CPU使用率
- メモリ使用量
- エラーログ

---

## 🆘 **8. 緊急時の連絡先**

### **技術サポート**
- **開発者**: Claude Code Assistant
- **リポジトリ**: https://github.com/Tenormusica2024/youtube-transcript-cloudrun
- **最終更新**: 2025-08-21 (コミット: 9774aff)

### **重要ファイル**
- **メインサーバー**: `production_server.py`
- **起動スクリプト**: `start_youtube_transcript_latest.bat`
- **設定ファイル**: `.env`
- **依存関係**: `requirements.txt`

---

## ✅ **9. 復旧完了の確認**

復旧が完了したら、以下を確認してください：

1. ✅ サーバーが http://127.0.0.1:8087 で応答
2. ✅ YouTube動画の字幕が抽出できる
3. ✅ フィラー除去機能が動作
4. ✅ Gemini AI要約が生成される
5. ✅ エラーなく継続的に稼働

**全ての項目が✅なら復旧完了です！**