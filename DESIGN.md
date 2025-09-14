# GPT-5 Podcast App - Cloud Run Design Document

## 概要
GPT-5のPodcast Homepageをベースに、Firebase Authentication、Cloud Storage、Firestoreを使用したpodcast配信プラットフォームを構築。

## アーキテクチャ

### 技術スタック
- **フロントエンド**: HTML/CSS/JS（GPT-5デザインベース）+ Firebase Auth SDK
- **バックエンド**: Python Flask + Firebase Admin SDK
- **認証**: Firebase Authentication (Email/Password + Google OAuth)
- **ファイル保存**: Cloud Storage (GCS) - private bucket + Signed URLs
- **データベース**: Firestore
- **デプロイ**: Cloud Run
- **CDN**: Cloud CDN（オプション、高トラフィック時）

### データフロー
```
1. ユーザーログイン (Firebase Auth)
2. MP3アップロード要求 → Cloud Run API
3. Signed URL発行 → ブラウザが直接GCSへアップロード
4. メタデータ登録 → Firestore
5. 再生時: Signed GET URL発行 → ブラウザで再生
```

## データ設計

### Firestore Collections

#### users/{uid}
```json
{
  "email": "user@example.com",
  "displayName": "User Name",
  "createdAt": "2025-01-01T00:00:00Z",
  "lastLogin": "2025-01-01T00:00:00Z",
  "storageUsed": 1048576,
  "maxStorageBytes": 1073741824,
  "role": "user"
}
```

#### tracks/{trackId}
```json
{
  "title": "Episode 1: Introduction",
  "description": "First episode of our podcast",
  "uploaderUid": "firebase_uid",
  "uploaderName": "User Name",
  "gcsPath": "users/firebase_uid/uuid.mp3",
  "originalFilename": "episode1.mp3",
  "durationSec": 1800,
  "sizeBytes": 25600000,
  "contentType": "audio/mpeg",
  "status": "approved",
  "visibility": "public",
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:00:00Z",
  "playCount": 0,
  "tags": ["intro", "podcast"],
  "thumbnailUrl": ""
}
```

#### playlists/{playlistId}
```json
{
  "title": "My Favorites",
  "description": "Collection of favorite episodes",
  "ownerUid": "firebase_uid",
  "ownerName": "User Name",
  "trackIds": ["track1", "track2", "track3"],
  "visibility": "private",
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-01-01T00:00:00Z"
}
```

## API設計

### Authentication
- `POST /api/auth/verify` - Firebase ID token検証
- `GET /api/auth/user` - 現在のユーザー情報取得

### Upload
- `POST /api/upload/signed-url` - アップロード用Signed URL発行
- `POST /api/tracks` - トラックメタデータ登録

### Tracks
- `GET /api/tracks` - トラック一覧（検索・フィルタ対応）
- `GET /api/tracks/{id}` - トラック詳細
- `GET /api/tracks/{id}/play-url` - 再生用Signed URL発行
- `PUT /api/tracks/{id}` - トラック情報更新
- `DELETE /api/tracks/{id}` - トラック削除

### Playlists
- `GET /api/playlists` - プレイリスト一覧
- `POST /api/playlists` - プレイリスト作成
- `PUT /api/playlists/{id}` - プレイリスト更新
- `DELETE /api/playlists/{id}` - プレイリスト削除

## セキュリティ

### 認証・認可
- 全API呼び出しでFirebase ID token検証
- ユーザーは自分のリソースのみアクセス可能
- 管理者権限による全体管理（将来実装）

### ファイル保護
- GCSバケットは非公開設定
- アップロード・再生はSigned URL経由のみ
- URL有効期限: アップロード15分、再生10分

### バリデーション
- ファイルサイズ上限: 100MB/ファイル
- ユーザー総容量上限: 1GB
- 対応フォーマット: MP3, M4A, WAV
- MIME type + magic bytes検証

## 運用設計

### スケーリング
- Cloud Run: 自動スケーリング（min: 0, max: 100）
- Firestore: 自動スケーリング
- Cloud Storage: 無制限

### 監視
- Cloud Logging: エラー・アクセスログ
- Cloud Monitoring: レスポンス時間・エラー率
- アラート: 高エラー率、異常アクセス

### バックアップ
- Firestore: 自動バックアップ設定
- Cloud Storage: バージョニング有効

## コスト最適化

### ストレージ
- 古い音源の自動アーカイブ（Nearline/Coldline）
- 未使用ファイルの定期削除

### 配信
- Cloud CDN導入でegress費用削減
- 適切なキャッシュヘッダ設定

## 実装フェーズ

### Phase 1: MVP
- Firebase Auth統合
- 基本的なアップロード機能
- シンプルな再生機能
- GPT-5デザインの移植

### Phase 2: 機能拡張
- プレイリスト機能
- 検索・フィルタ機能
- ユーザープロファイル

### Phase 3: 高度な機能
- 音声処理（正規化、メタデータ抽出）
- ソーシャル機能（いいね、コメント）
- 分析ダッシュボード

## 開発環境

### ローカル開発
```bash
# Firebase Emulator Suite
firebase emulators:start

# Flask開発サーバー
python app.py

# フロントエンド
# 静的ファイルとして配信またはlive-server
```

### 本番環境
```bash
# Cloud Runデプロイ
gcloud run deploy podcast-app \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```