# YouTube Transcript Extractor - アイコンファイル

この拡張機能で使用するアイコンファイルを配置するディレクトリです。

## 必要なアイコンサイズ

以下のサイズのPNGファイルが必要です：

- `icon-16.png` (16x16px) - 拡張機能メニュー用
- `icon-32.png` (32x32px) - Windows用
- `icon-48.png` (48x48px) - 拡張機能管理画面用
- `icon-128.png` (128x128px) - Chrome Web Store用

## アイコンデザイン

- **テーマ**: YouTubeの赤色（#FF0000）をベースとした字幕・テキストアイコン
- **スタイル**: モダン、フラットデザイン
- **シンボル**: 動画プレイヤーと字幕テキストを組み合わせたデザイン

## 一時的なアイコン作成方法

アイコンファイルが用意できない場合の代替手順：

1. **オンラインアイコンジェネレーター使用**
   - https://www.favicon-generator.org/
   - https://realfavicongenerator.net/

2. **手動作成（CSS/HTML）**
   ```html
   <div style="width:128px;height:128px;background:#ff0000;border-radius:20px;display:flex;align-items:center;justify-content:center;color:white;font-size:60px;">📺</div>
   ```

3. **Canvaまたは類似ツール使用**
   - 128x128pxのキャンバス作成
   - 赤色背景（#FF0000）
   - 白色のテキスト/字幕アイコン追加

## 拡張機能ロード方法

アイコンファイルが準備できたら：

1. Chrome拡張機能管理ページを開く（`chrome://extensions/`）
2. 「デベロッパーモード」を有効化
3. 「パッケージ化されていない拡張機能を読み込む」をクリック
4. `chrome-extension`フォルダを選択

## アイコン作成後の確認事項

- [ ] すべてのサイズ（16, 32, 48, 128px）のPNGファイルが存在
- [ ] 透明背景または適切な背景色
- [ ] 各サイズで視認性が良好
- [ ] Chrome拡張機能として正常に読み込み可能