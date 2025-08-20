# YouTube字幕抽出ツール（ハイブリッド版）

## 概要

YouTube動画の字幕をローカルで抽出し、Cloud Run APIを使ってGemini AIで整形・要約するハイブリッド型ツールです。

## 特徴

- **ローカル字幕抽出**: YouTube Transcript APIを使用してローカルで字幕を取得
- **AI整形・要約**: Cloud Run APIを通じてGemini AIで読みやすく整形・要約
- **多言語対応**: 日本語、英語、韓国語、中国語、スペイン語、フランス語、ドイツ語、自動検出
- **複数API対応**: Cloud Run、ローカルサーバー、カスタムURL
- **ファイル保存**: テキスト形式とJSON形式で結果を保存

## ファイル構成

```
youtube_transcript_webapp/
├── hybrid_transcript_tool.py    # メインスクリプト
├── start_hybrid_tool.bat        # Windows用起動バッチファイル
├── test_simple.py               # テスト用スクリプト
├── standalone.html              # スタンドアロンHTMLページ
├── app.py                       # Flask APIサーバー
└── requirements.txt             # Python依存関係
```

## 使用方法

### 1. バッチファイルから起動（推奨）

```cmd
start_hybrid_tool.bat
```

### 2. Pythonから直接実行

```bash
cd youtube_transcript_webapp
python hybrid_transcript_tool.py
```

### 3. 対話的な使用手順

1. YouTube URLまたは動画IDを入力
2. 字幕言語を選択（1-8）
3. APIサーバーを選択（1-3）
4. 処理完了後、結果ファイルを確認

## APIサーバーオプション

1. **Cloud Run (推奨)**: `https://yt-transcript-ycqe3vmjva-uc.a.run.app`
   - Gemini AIによる高品質な整形・要約
   - 常時利用可能

2. **ローカルサーバー**: `http://localhost:8080`
   - app.pyが起動している必要がある
   - 開発・テスト用

3. **カスタムURL**: 任意のAPI URL
   - 独自のAPIサーバーを使用

## 出力ファイル

### テキストファイル
- ファイル名: `transcript_{動画ID}_{タイムスタンプ}.txt`
- 内容: AI整形済み字幕 + AI要約

### JSONファイル
- ファイル名: `transcript_{動画ID}_{タイムスタンプ}.json`
- 内容: 構造化されたデータ（メタデータ、整形済み字幕、要約、生データ）

## 依存関係

```
youtube-transcript-api==1.2.2
requests
```

## テスト

基本機能のテスト：
```bash
python test_simple.py
```

## トラブルシューティング

### 字幕取得エラー
- 動画に字幕が存在するか確認
- プライベート動画でないか確認
- 異なる言語設定を試す

### API通信エラー
- インターネット接続を確認
- APIサーバーのステータスを確認
- ファイアウォール設定を確認

### 文字化け
- Windows環境では文字エンコーディングの問題が発生する可能性があります
- コマンドプロンプトの文字コードを確認してください

## 更新履歴

- 2025-08-17: ハイブリッド版リリース
  - ローカル抽出 + Cloud Run AI機能
  - 新APIバージョン（1.2.2）対応
  - 文字エンコーディング問題修正

## ライセンス

このツールは教育・研究目的で使用してください。YouTubeの利用規約を遵守してください。