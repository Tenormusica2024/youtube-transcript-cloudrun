# 🎬 YouTube Transcript Extractor

YouTube動画の字幕を自動抽出・AI要約するWebアプリケーション + ブラウザ拡張機能

## 🚀 簡単インストール（30秒）

**最も簡単な方法: Tampermonkey版**
1. [Tampermonkey拡張機能](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)をインストール
2. [ワンクリックインストール](./tampermonkey-userscript.js) - 自動でYouTubeに字幕抽出ボタンが追加されます

**その他の方法**: Chrome拡張機能版、CRXダイレクト版も利用可能  
📋 **詳細な手順**: [install_instructions.html](./install_instructions.html)

## ✨ 主要機能

### 🎯 **ブラウザ拡張機能**
- **YouTube UI統合**: 動画プレイヤー下部に字幕抽出ボタンを自動追加
- **ワンクリック抽出**: ボタンクリックで即座に字幕抽出・AI要約
- **包括的対応**: YouTube通常動画・Shorts・モバイル版に対応
- **設定管理**: サーバーURL設定、通知機能

### 🤖 **AI要約・整形機能**  
- **Google Gemini AI**: 高品質な要約とマークダウン整形
- **多言語対応**: 日本語・英語・その他言語の字幕に対応
- **カスタム要約**: 要約の詳細度を調整可能
- **構造化出力**: 見出し、要点、タイムスタンプ付き

### ⚡ **高性能・高可用性**
- **レスポンシブデザイン**: PC・スマートフォン・タブレット対応
- **フォールバック機能**: 複数の字幕取得方法で高い成功率
- **レート制限**: 適切なAPI使用量管理
- **セキュリティ**: CORS対応、入力検証

## 📱 対応プラットフォーム

### **ブラウザ拡張機能**
- **Google Chrome** (推奨) - Manifest V3完全対応
- **Microsoft Edge** - Chromiumベース、同等機能
- **Brave Browser** - Chrome拡張機能互換
- **Opera** - Chrome拡張機能サポート

### **Webアプリケーション**
- **デスクトップ**: Windows, macOS, Linux
- **モバイル**: iOS Safari, Android Chrome
- **タブレット**: iPad, Android タブレット

## 🛠️ 技術スタック

### **フロントエンド**
- **HTML5/CSS3**: レスポンシブデザイン
- **JavaScript (ES6+)**: モダンブラウザ対応
- **Chrome Extension APIs**: Manifest V3準拠

### **バックエンド**
- **Python 3.8+**: Flask/FastAPI
- **Google Gemini API**: AI要約・整形
- **YouTube Transcript API**: 字幕データ取得

### **インフラ**
- **Google Cloud Run**: サーバーレス実行環境
- **GitHub Pages**: 静的サイトホスティング
- **Docker**: コンテナ化デプロイ

## 📊 配布方法比較

| 方法 | 簡単さ | 所要時間 | 技術知識 | 機能 | おすすめ度 |
|------|--------|----------|----------|------|------------|
| **Tampermonkey版** | ⭐⭐⭐⭐⭐ | 30秒 | 不要 | 基本機能 | ⭐⭐⭐⭐⭐ |
| **Chrome拡張機能版** | ⭐⭐⭐⭐ | 1分 | 最小限 | 全機能 | ⭐⭐⭐⭐ |
| **CRXダイレクト版** | ⭐⭐⭐ | 1分 | 中程度 | 全機能 | ⭐⭐⭐ |
| **Webアプリ単体** | ⭐⭐ | 即座 | 不要 | 手動操作 | ⭐⭐ |

## 🔧 開発者向け情報

### **ローカル開発**
```bash
# 1. リポジトリクローン
git clone https://github.com/Tenormusica2024/youtube-transcript-cloudrun.git
cd youtube-transcript-cloudrun

# 2. 仮想環境作成・依存関係インストール
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. サーバー起動
python app_mobile.py
# サーバー: http://localhost:8085

# 4. Chrome拡張機能テスト
# Chrome拡張機能管理ページで chrome-extension/ フォルダを読み込み
```

### **ビルド・パッケージング**
```bash
# 全配布パッケージ生成
python build_crx.py

# 生成物 (dist/ フォルダ)
# - youtube-transcript-extractor-v1.0.0.zip (Chrome拡張機能)
# - youtube-transcript-extractor-v1.0.0.crx (ダイレクトインストール)
# - youtube-transcript-extractor.user.js (Tampermonkey)
# - index.html (インストールページ)
# - checksums.txt (ファイル検証)
```

### **拡張機能開発**
```javascript
// manifest.json - Chrome拡張機能設定
{
  "manifest_version": 3,
  "name": "YouTube Transcript Extractor",
  "version": "1.0.0",
  "permissions": ["activeTab", "scripting", "storage"],
  "content_scripts": [{
    "matches": ["https://www.youtube.com/watch*", "https://www.youtube.com/shorts/*"],
    "js": ["content.js"],
    "css": ["youtube-integration.css"]
  }]
}
```

## 🔒 セキュリティ・プライバシー

### **データ保護**
- **収集なし**: ユーザーデータの外部送信なし
- **ローカル処理**: 設定データはブラウザ内保存
- **通信先限定**: 指定したサーバーURLのみ
- **HTTPS強制**: セキュアな通信のみ

### **権限要求**
- `activeTab`: 現在のタブのURL取得のみ
- `scripting`: YouTubeページへのDOM操作のみ
- `storage`: 設定データの保存のみ

## 📝 ライセンス

MIT License - 自由に使用・改変・配布可能

## 🤝 コントリビューション

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## 📞 サポート

- **Issues**: [GitHub Issues](https://github.com/Tenormusica2024/youtube-transcript-cloudrun/issues)
- **Discord**: [サポートサーバー](https://discord.gg/your-server) (準備中)
- **Email**: support@youtube-transcript.io (準備中)

## 🌟 謝辞

- **Google Gemini AI**: 高品質なAI要約機能
- **YouTube Transcript API**: 字幕データ提供
- **Chrome Extension Community**: 技術参考・フィードバック

---

**YouTube Transcript Extractor Team**  
**Version**: 1.0.0  
**Last Updated**: 2025-08-17
