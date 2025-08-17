# 🚨 YouTube Transcript WebApp - 緊急復旧手順書

## 緊急時概要

このドキュメントは深刻なエラー、システム障害、または予期しない問題が発生した際に、YouTube Transcript WebAppを安全で動作確認済みの状態に即座に復旧するためのガイドです。

**安全な復旧ポイント**: `v2.1.0-stable-shorts`

---

## 🆘 即座実行: 自動復旧

### ワンクリック復旧
```batch
# プロジェクトディレクトリに移動して実行
cd "C:\Users\Tenormusica\youtube_transcript_webapp"
.\rollback_to_stable.bat
```

**復旧時間**: < 5分  
**総所要時間**: < 15分（検証含む）

---

## 📋 緊急復旧チェックリスト

### 🔴 Level 1: 即座対応（< 2分）
- [ ] 現在のエラー状況を記録
- [ ] 自動復旧スクリプト実行: `.\rollback_to_stable.bat`
- [ ] スクリプト実行完了まで待機

### 🟡 Level 2: 基本確認（2-5分）
- [ ] サーバー起動確認: `python app_mobile.py`
- [ ] ローカルアクセス確認: http://localhost:8085
- [ ] ヘルスチェック確認: http://localhost:8085/health

### 🟢 Level 3: 機能検証（5-15分）
- [ ] YouTube通常動画URL テスト
- [ ] YouTube Shorts URL テスト
- [ ] AI字幕整形機能テスト
- [ ] API エンドポイント動作確認

---

## 🛠️ 手動復旧手順（自動復旧失敗時）

### Step 1: 安全な状態への復帰
```bash
cd "C:\Users\Tenormusica\youtube_transcript_webapp"

# 現在の変更をバックアップ
git add .
git commit -m "Emergency backup before manual rollback"

# 安定版タグにロールバック
git checkout v2.1.0-stable-shorts

# 作業ブランチ作成
git checkout -b manual-emergency-rollback-$(date +%Y%m%d-%H%M)
```

### Step 2: 依存関係復旧
```bash
# Python依存関係
pip install -r requirements.txt

# Node.js依存関係（該当する場合）
npm install
```

### Step 3: 動作確認
```bash
# テストスイート実行
python test_shorts_support.py

# サーバー起動テスト
python app_mobile.py
```

---

## 🧪 復旧後検証項目

### 必須検証項目
1. **サーバー起動**: `python app_mobile.py` が正常に起動
2. **ヘルスチェック**: http://localhost:8085/health が200応答
3. **YouTube通常動画**: 字幕抽出が正常動作
4. **YouTube Shorts**: 新機能が正常動作

### 検証用テストURL
```
# 通常動画
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# YouTube Shorts  
https://www.youtube.com/shorts/dQw4w9WgXcQ

# 短縮URL
https://youtu.be/dQw4w9WgXcQ
```

### 期待される結果
- ✅ 全てのURL形式で動画IDが正常に抽出される
- ✅ 字幕データが取得される
- ✅ AI整形機能が動作する
- ✅ エラーハンドリングが適切に機能する

---

## 📊 復旧状況確認コマンド

### Git状態確認
```bash
# 現在のブランチとコミット確認
git branch
git log --oneline -5

# 安定版タグ確認
git tag -l | grep stable

# ファイル変更状況確認
git status
```

### アプリケーション状態確認
```bash
# バージョン情報確認
cat VERSION_METADATA.json

# 重要ファイル存在確認
ls -la app*.py
ls -la test_shorts_support.py
ls -la rollback_to_stable.bat

# ログファイル確認
ls -la *.log
```

---

## 🔧 一般的な問題と解決方法

### 問題1: 依存関係エラー
```bash
# 仮想環境再作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 問題2: ポート競合エラー
```bash
# 使用中プロセス確認・停止
netstat -ano | findstr :8085
taskkill /PID <PID> /F

# 別ポートで起動
python app_mobile.py --port 8086
```

### 問題3: API キーエラー
```bash
# 環境変数確認
echo $GEMINI_API_KEY
echo $YOUTUBE_API_KEY

# .envファイル確認
cat .env
```

### 問題4: Git関連エラー
```bash
# Git状態リセット
git reset --hard v2.1.0-stable-shorts
git clean -fd

# 強制的にタグ状態に戻す
git checkout --force v2.1.0-stable-shorts
```

---

## 📞 エスカレーション基準

### 自動復旧が不可能な場合
- [ ] 上記手動復旧手順を全て実行済み
- [ ] 復旧後検証で複数項目が失敗
- [ ] システム全体に影響する重大な問題

### エスカレーション情報収集
```bash
# システム情報収集
python --version
git --version
pip list
git log --oneline -10

# エラーログ収集
cat error.log
cat server_startup.log
cat test_results_rollback.log
```

---

## 📈 復旧成功の確認

### 復旧完了の判定基準
1. **サーバー起動**: ✅ 正常に起動、エラーなし
2. **ヘルスチェック**: ✅ 200応答、全サービス正常
3. **URL解析**: ✅ 14種類のURL形式で85%以上の成功率
4. **Shorts対応**: ✅ `/shorts/VIDEO_ID` 形式の正常処理
5. **AI機能**: ✅ 字幕整形・要約機能の正常動作

### 復旧完了時の状態
- **Gitタグ**: v2.1.0-stable-shorts
- **ブランチ**: emergency-rollback-YYYYMMDD または manual-emergency-rollback-YYYYMMDD-HHMM
- **機能状態**: YouTube Shorts対応、App Store最適化済み
- **セキュリティ**: セキュリティヘッダー、SSL対応
- **パフォーマンス**: キャッシュ、圧縮、レート制限有効

---

## 🔒 セキュリティ考慮事項

### 復旧時の注意点
- [ ] API キーの漏洩がないことを確認
- [ ] ログファイルに機密情報が含まれていないことを確認
- [ ] バックアップブランチの適切な管理
- [ ] セキュリティヘッダーの有効性確認

### 復旧後の推奨アクション
- [ ] セキュリティスキャンの実行
- [ ] アクセスログの確認
- [ ] 監視アラートの確認
- [ ] インシデント報告書の作成

---

## 📝 復旧記録テンプレート

```
=== 緊急復旧記録 ===
日時: [復旧実行日時]
復旧担当者: [担当者名]
障害内容: [発生した問題の詳細]
復旧方法: [自動復旧/手動復旧]
復旧時間: [開始時刻] - [完了時刻]
検証結果: [テスト結果詳細]
残課題: [未解決の問題があれば記載]
予防策: [今後の対応策]
```

---

**🆘 この手順書に従って復旧が困難な場合は、システム管理者にエスカレーションしてください。**

**最終更新**: 2025-08-17  
**復旧保証バージョン**: v2.1.0-stable-shorts  
**推定復旧時間**: < 15分