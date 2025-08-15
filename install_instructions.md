# YouTube AI要約ツール インストール手順

## 🚀 かんたん3ステップ

### ステップ1: Tampermonkey拡張機能をインストール
- [Chrome用](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
- [Edge用](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)
- [Firefox用](https://addons.mozilla.org/firefox/addon/tampermonkey/)

### ステップ2: スクリプトをインストール
1. Tampermonkeyアイコンをクリック → 「新規スクリプトを作成」
2. 既存のコードを全て削除
3. `tampermonkey_script.js` の内容を全てコピー＆ペースト
4. Ctrl+S で保存

### ステップ3: YouTubeで使用
1. YouTubeで好きな動画を開く
2. **右下に「🤖 AI要約」ボタンが自動で表示されます**
3. ボタンをクリックすると自動で要約が生成されます

## 📝 動作の仕組み

```
YouTube動画ページ
    ↓
[🤖 AI要約] ボタン（自動追加）
    ↓
クリック
    ↓
1. 字幕を自動取得（クライアント側）
2. Cloud Runサーバーに送信
3. Gemini AIで要約生成
4. 結果をポップアップ表示
```

## ⚠️ 注意事項
- 字幕がある動画のみ対応
- ライブ配信は非対応
- 初回は数秒かかります

## 🔧 トラブルシューティング

### ボタンが表示されない場合
1. Tampermonkeyが有効か確認
2. ページをリロード（F5）
3. YouTubeのURLが `https://www.youtube.com/watch` で始まっているか確認

### エラーが出る場合
- 「この動画には字幕がありません」→ 字幕付き動画でお試しください
- 「サーバーエラー」→ しばらく待ってから再試行

## 🎉 完了！
これで、YouTubeを見ながらワンクリックでAI要約が使えます！