# YouTube Transcript Extractor - Chrome拡張機能

YouTube動画プレイヤーの下部に字幕抽出ボタンを追加する Chrome/Edge 拡張機能です。

## 🎯 機能概要

### 主要機能
- **YouTube UI統合**: 動画プレイヤー下部の操作エリアに字幕抽出ボタンを追加
- **ワンクリック抽出**: ボタンクリックで即座に字幕抽出ツールを起動
- **包括的対応**: YouTube通常動画・Shorts・モバイル版に対応
- **サーバー設定**: ローカル・ngrok・本番環境サーバーに対応

### 挿入ポイント
1. **プレイヤーコントロール右側** - 設定ボタン近く（優先度: 高）
2. **動画タイトル下のボタンエリア** - いいね・共有ボタン群（優先度: 中）
3. **アクションコンテナ** - 動画情報エリア（優先度: 中）
4. **プレイヤー下部** - 独立コンテナ（フォールバック）

## 📁 ファイル構成

```
chrome-extension/
├── manifest.json          # 拡張機能の設定ファイル
├── content.js             # YouTube UI統合メインスクリプト
├── youtube-integration.css # YouTube UI用カスタムスタイル
├── popup.html             # 拡張機能ポップアップUI
├── popup.js               # ポップアップ制御スクリプト
├── background.js          # バックグラウンドサービスワーカー
├── icons/                 # アイコンファイル（要準備）
│   ├── icon-16.png
│   ├── icon-32.png
│   ├── icon-48.png
│   └── icon-128.png
└── README.md              # この説明書
```

## 🛠️ インストール手順

### 1. アイコンファイル準備
```bash
cd chrome-extension/icons/
# 16, 32, 48, 128px のPNGアイコンファイルを配置
# 詳細は icons/README.md を参照
```

### 2. Chrome拡張機能として読み込み
1. Chromeで `chrome://extensions/` を開く
2. 右上の「デベロッパーモード」を有効化
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. `chrome-extension` フォルダを選択

### 3. 字幕抽出サーバー起動
```bash
cd ../
python app_mobile.py
# デフォルト: http://localhost:8085
```

## 🚀 使用方法

### 基本操作
1. **YouTube動画ページに移動** - 通常動画またはShorts
2. **字幕抽出ボタンをクリック** - プレイヤー操作エリア内に表示
3. **自動字幕抽出** - 新しいタブで字幕抽出ツールが起動

### 拡張機能ポップアップ
- **拡張機能アイコンクリック** - 詳細設定・手動操作
- **サーバーURL設定** - localhost/ngrok/本番環境切り替え
- **接続テスト** - サーバー稼働状況確認
- **手動字幕抽出** - ポップアップから直接実行

### コンテキストメニュー
- **右クリックメニュー** - 「字幕を抽出・要約」オプション
- **リンク右クリック** - YouTubeリンクから直接抽出

## 🎨 UI統合詳細

### ボタンスタイル
- **プレイヤーコントロール内**: 半透明・小型・アイコン重視
- **トップレベルボタン**: YouTube標準ボタンスタイル
- **アクションエリア**: 赤色グラデーション・目立つデザイン
- **プレイヤー下部**: 独立コンテナ・フォールバック表示

### DOM監視システム
- **MutationObserver**: YouTube SPA対応の動的DOM監視
- **イベントリスナー**: `yt-navigate-finish` イベント対応
- **自動再挿入**: 動画変更時の自動ボタン再配置
- **重複防止**: 既存ボタンの自動削除・更新

### レスポンシブ対応
- **デスクトップ**: フル機能ボタン表示
- **モバイル**: 縮小ボタン・タッチ操作最適化
- **ダークモード**: YouTube標準テーマ連動

## ⚙️ 設定オプション

### chrome.storage.sync 設定
```javascript
{
  "serverUrl": "http://localhost:8085",    // サーバーURL
  "autoExtract": false,                    // 自動抽出有効化
  "defaultLanguage": "ja"                  // デフォルト字幕言語
}
```

### サーバーURL設定例
- **ローカル開発**: `http://localhost:8085`
- **ngrokトンネル**: `https://abc123.ngrok-free.app`
- **本番環境**: `https://your-domain.com`

## 🔧 カスタマイズ

### ボタン位置調整
`content.js` の `insertionStrategies` 配列で優先順位変更:
```javascript
const insertionStrategies = [
    () => this.insertIntoControlsRight(),    // 最優先
    () => this.insertIntoTopLevelButtons(),  // 2番目
    () => this.insertIntoPlayerActions(),    // 3番目
    () => this.insertBelowPlayer()           // フォールバック
];
```

### スタイル変更
`youtube-integration.css` でボタン外観をカスタマイズ:
```css
.yte-transcript-btn-action:hover {
    background: linear-gradient(135deg, #your-color 0%, #your-color-dark 100%);
}
```

## 🐛 トラブルシューティング

### ボタンが表示されない
1. **拡張機能が有効** - `chrome://extensions/` で確認
2. **YouTube動画ページ** - URLパターン確認
3. **DOM読み込み完了** - ページ再読み込み試行
4. **コンソールエラー** - DevTools でエラー確認

### サーバー接続エラー
1. **サーバー起動確認** - `http://localhost:8085/health`
2. **CORS設定** - `app_mobile.py` のCORS設定確認
3. **ファイアウォール** - ローカルサーバーアクセス許可
4. **URL設定** - ポップアップでサーバーURL確認

### YouTube UI変更対応
1. **セレクター更新** - `content.js` のDOM要素セレクター確認
2. **スタイル調整** - `youtube-integration.css` の調整
3. **監視対象追加** - `observeYouTubeChanges()` の監視対象拡張

## 📱 対応ブラウザ

- **Google Chrome** (推奨) - Manifest V3完全対応
- **Microsoft Edge** - Chromiumベース、同等機能
- **Brave Browser** - Chrome拡張機能互換
- **Opera** - Chrome拡張機能サポート

## 🔒 セキュリティ・プライバシー

### 権限要求
- `activeTab` - 現在のタブの URL取得のみ
- `scripting` - YouTube ページへの DOM操作のみ
- `storage` - 設定データの保存のみ

### データ収集
- **収集なし** - ユーザーデータの外部送信なし
- **ローカル処理** - 設定データはブラウザ内保存
- **通信先限定** - 指定したサーバーURLのみ

## 🚀 今後の拡張予定

- **Safari拡張機能** - macOS/iOS Safari対応
- **Firefox拡張機能** - WebExtensions API対応
- **高度な設定** - ショートカットキー・自動実行設定
- **統計機能** - 抽出回数・使用状況の可視化

---

**開発者**: YouTube Transcript Extractor Team  
**バージョン**: 1.0.0  
**最終更新**: 2025-08-17