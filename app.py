import base64
import io
import json
import os
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote

import feedparser
import firebase_admin
import magic
import requests
from firebase_admin import auth, credentials
from flask import Flask, jsonify, redirect, render_template, request, session
from flask_cors import CORS
from google.cloud import firestore, storage
from mutagen import File as MutagenFile
from mutagen.id3 import ID3NoHeaderError
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

# CORS設定
CORS(app, origins=["*"])

# 定数
DEFAULT_BIO_MESSAGE = "このユーザーはまだプロフィール説明を設定していません。"


# セキュリティヘッダー設定
@app.after_request
def add_security_headers(response):
    """セキュリティヘッダーを全レスポンスに追加"""
    # Content Security Policy - XSS攻撃を防御
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "media-src 'self' https: blob:; "
        "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com; "
        "frame-ancestors 'none'; "
        "form-action 'self';"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    # フレーム埋め込み防止
    response.headers["X-Frame-Options"] = "DENY"

    # MIME Typeスナッフィング防止
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection（レガシーブラウザ用）
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Referrer Policy - プライバシー保護
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # HTTPS強制（本番環境のみ）
    if not app.debug and request.is_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    # Permissions Policy - 不要な機能へのアクセス制限
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=()"
    )

    return response


# HTTPS強制リダイレクト（本番環境のみ）
@app.before_request
def force_https():
    """本番環境でHTTPS接続を強制"""
    if not app.debug and request.headers.get("X-Forwarded-Proto") == "http":
        return redirect(request.url.replace("http://", "https://"), code=301)


# グローバルエラーハンドラー
@app.errorhandler(400)
def bad_request(error):
    """400エラーハンドラー"""
    app.logger.warning(f"Bad request: {error}")
    return (
        jsonify(
            {
                "error": "不正なリクエストです",
                "details": "リクエストの形式を確認してください",
            }
        ),
        400,
    )


@app.errorhandler(401)
def unauthorized(error):
    """401エラーハンドラー"""
    app.logger.warning(f"Unauthorized access: {error}")
    return (
        jsonify(
            {
                "error": "認証が必要です",
                "details": "有効な認証トークンを提供してください",
            }
        ),
        401,
    )


@app.errorhandler(403)
def forbidden(error):
    """403エラーハンドラー"""
    app.logger.warning(f"Forbidden access: {error}")
    return (
        jsonify(
            {
                "error": "アクセスが拒否されました",
                "details": "このリソースにアクセスする権限がありません",
            }
        ),
        403,
    )


@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラー"""
    return (
        jsonify(
            {
                "error": "リソースが見つかりません",
                "details": "リクエストされたリソースが存在しません",
            }
        ),
        404,
    )


@app.errorhandler(429)
def rate_limit_exceeded(error):
    """429エラーハンドラー"""
    app.logger.warning(f"Rate limit exceeded: {error}")
    return (
        jsonify(
            {
                "error": "レート制限に達しました",
                "details": "しばらく時間をおいてから再試行してください",
            }
        ),
        429,
    )


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    app.logger.error(f"Internal server error: {error}")
    return (
        jsonify(
            {
                "error": "サーバー内部エラーが発生しました",
                "details": "管理者にお問い合わせください",
            }
        ),
        500,
    )


# Google Cloud設定
# 🚨 CRITICAL: プロジェクト名とバケット名が一致しないとGCS 500エラーが発生します
# - 環境変数 GOOGLE_CLOUD_PROJECT と STORAGE_BUCKET が正しく設定されている必要があります
# - バケットが存在しない場合: gcloud storage buckets create gs://{BUCKET_NAME} --location=asia-northeast1
# - 権限が不足している場合: gcloud projects add-iam-policy-binding {PROJECT_ID} --member="serviceAccount:{PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/storage.objectAdmin"
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "yt-transcript-demo-2025")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", f"{PROJECT_ID}-podcast-audio")

# Firebase Admin初期化
if not firebase_admin._apps:
    try:
        # Cloud Runではサービスアカウントが自動的に使用される
        # ローカル開発時は GOOGLE_APPLICATION_CREDENTIALS 環境変数を設定
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(
            cred,
            {
                "projectId": PROJECT_ID,
            },
        )
        print("✅ Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"⚠️ Firebase Admin SDK initialization failed: {e}")
        print("🔧 Running without Firebase Admin SDK (mock mode)")

# クライアント初期化
try:
    storage_client = storage.Client()
    print("✅ Google Cloud Storage client initialized")
except Exception as e:
    print(f"⚠️ Storage client initialization failed: {e}")
    storage_client = None

# Firestore初期化
# 🚨 CRITICAL: プレイリスト機能500エラーの主要原因
# - Firestore APIが有効化されていない場合: gcloud services enable firestore.googleapis.com --project={PROJECT_ID}
# - Firestoreデータベースが未作成の場合: gcloud firestore databases create --location=asia-northeast1 --project={PROJECT_ID}
# - エラーメッセージ例: "Cloud Firestore API has not been used in project before or it is disabled"
try:
    db = firestore.Client()
    print("✅ Firestore client initialized")
except Exception as e:
    print(f"⚠️ Firestore client initialization failed: {e}")
    print("💡 Fix: Enable Firestore API and create database (see comments above)")
    db = None

# 設定
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB（動画対応のため増量）
MAX_USER_STORAGE = 5 * 1024 * 1024 * 1024  # 5GB（動画対応のため増量）
ALLOWED_MIME_TYPES = [
    # 音声ファイル
    "audio/mpeg",
    "audio/mp4",
    "audio/wav",
    "audio/x-wav",
    "audio/aac",
    "audio/flac",
    # 動画ファイル
    "video/mp4",
    "video/webm",
    "video/avi",
    "video/quicktime",
    "video/x-msvideo",
]
ALLOWED_EXTENSIONS = [
    # 音声拡張子
    ".mp3",
    ".m4a",
    ".wav",
    ".aac",
    ".flac",
    # 動画拡張子
    ".mp4",
    ".webm",
    ".avi",
    ".mov",
]

# レート制限設定
RATE_LIMIT_REQUESTS = 100  # 1時間あたりのリクエスト数
RATE_LIMIT_WINDOW = 3600  # 1時間（秒）
rate_limit_storage = defaultdict(list)


def get_client_ip():
    """クライアントIPアドレスを取得（プロキシ対応）"""
    return request.headers.get("X-Forwarded-For", request.remote_addr)


def rate_limit_decorator(max_requests=RATE_LIMIT_REQUESTS, window=RATE_LIMIT_WINDOW):
    """レート制限デコレータ"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = get_client_ip()
            current_time = time.time()

            # 古いリクエスト記録を削除
            rate_limit_storage[client_ip] = [
                req_time
                for req_time in rate_limit_storage[client_ip]
                if current_time - req_time < window
            ]

            # リクエスト数チェック
            if len(rate_limit_storage[client_ip]) >= max_requests:
                app.logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return (
                    jsonify(
                        {
                            "error": "レート制限に達しました。しばらく時間をおいてから再試行してください。",
                            "retry_after": window,
                        }
                    ),
                    429,
                )

            # 現在のリクエストを記録
            rate_limit_storage[client_ip].append(current_time)

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def validate_string_input(
    value, field_name, min_length=1, max_length=255, allow_empty=False
):
    """文字列入力の検証"""
    if value is None:
        if not allow_empty:
            raise ValueError(f"{field_name}は必須です")
        return ""

    if not isinstance(value, str):
        raise ValueError(f"{field_name}は文字列である必要があります")

    value = value.strip()

    if not allow_empty and len(value) < min_length:
        raise ValueError(f"{field_name}は{min_length}文字以上で入力してください")

    if len(value) > max_length:
        raise ValueError(f"{field_name}は{max_length}文字以内で入力してください")

    # 危険な文字列パターンをチェック
    dangerous_patterns = [
        r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValueError(f"{field_name}に不正な内容が含まれています")

    return value


def validate_filename(filename):
    """ファイル名の検証"""
    if not filename:
        raise ValueError("ファイル名は必須です")

    # 危険なパスやファイル名パターンをチェック
    dangerous_patterns = [
        r"\.\./",  # Path traversal
        r"\.\.\\",  # Path traversal (Windows)
        r"^\./",  # Hidden files
        r'[<>:"|?*]',  # Windows invalid characters
        r"[\x00-\x1f]",  # Control characters
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, filename):
            raise ValueError("ファイル名に不正な文字が含まれています")

    # ファイル拡張子チェック
    allowed_extensions = [
        # 音声拡張子
        ".mp3",
        ".m4a",
        ".wav",
        ".flac",
        ".aac",
        # 動画拡張子
        ".mp4",
        ".webm",
        ".avi",
        ".mov",
    ]
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext not in allowed_extensions:
        raise ValueError(
            f'対応していないファイル形式です。対応形式: {", ".join(allowed_extensions)}'
        )

    return filename


def validate_positive_integer(value, field_name, max_value=None):
    """正の整数の検証"""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError(f"{field_name}は正の数値である必要があります")

    if max_value and value > max_value:
        raise ValueError(f"{field_name}は{max_value}以下である必要があります")

    return int(value)


def ensure_user_library(user_uid):
    """ユーザーの個人ライブラリが存在することを確認し、なければ作成"""
    if db is None:
        return False

    try:
        user_library_ref = db.collection("user_libraries").document(user_uid)
        user_library_doc = user_library_ref.get()

        if not user_library_doc.exists:
            # 個人ライブラリを初期化
            user_library_ref.set(
                {
                    "userId": user_uid,
                    "savedTracks": [],
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow(),
                }
            )
            app.logger.info(f"✅ Personal library initialized for user {user_uid}")
            return True
        return True
    except Exception as e:
        app.logger.error(f"❌ Failed to ensure user library for {user_uid}: {e}")
        return False


def verify_token(f):
    """Firebase ID token検証デコレータ"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header required"}), 401

        token = auth_header.split(" ")[1]

        # 開発用モックトークンの場合はバイパス
        if token.startswith("mock-token-for-development"):
            # 拡張されたモックトークンの場合、ユーザー情報を抽出
            if ":" in token:
                try:
                    import base64
                    import json

                    token_parts = token.split(":")
                    user_data_b64 = token_parts[1]
                    user_data = json.loads(
                        base64.b64decode(user_data_b64).decode("utf-8")
                    )

                    request.user_uid = user_data.get("uid")
                    request.user_email = user_data.get("email")
                    request.user_name = user_data.get(
                        "displayName",
                        (
                            request.user_email.split("@")[0]
                            if request.user_email
                            else "User"
                        ),
                    )

                    # デバッグログでユーザーIDを確認
                    app.logger.info(
                        f"Authenticated user: uid={request.user_uid}, email={request.user_email}"
                    )
                except Exception as e:
                    app.logger.warning(f"Failed to parse mock token user data: {e}")
                    # フォールバックでデフォルト値を使用
                    request.user_uid = "mock-user-dev"
                    request.user_email = "dev@example.com"
                    request.user_name = "Development User"
                    app.logger.info(
                        f"Using fallback user: uid={request.user_uid}, email={request.user_email}"
                    )
            else:
                # レガシーモックトークンの場合
                request.user_uid = "mock-user-dev"
                request.user_email = "dev@example.com"
                request.user_name = "Development User"
                app.logger.info(
                    f"Using legacy mock user: uid={request.user_uid}, email={request.user_email}"
                )

            return f(*args, **kwargs)

        try:
            # Firebase Admin SDKが利用可能な場合のみ検証
            if firebase_admin._apps:
                app.logger.info(f"🔑 Verifying Firebase token: {token[:20]}...")
                decoded_token = auth.verify_id_token(token)
                request.user_uid = decoded_token["uid"]
                request.user_email = decoded_token.get("email", "")
                request.user_name = decoded_token.get(
                    "name", decoded_token.get("email", "").split("@")[0]
                )
                app.logger.info(
                    f"✅ Token verified successfully: uid={request.user_uid}, email={request.user_email}"
                )
            else:
                # Firebase Admin SDKが利用できない場合はデバッグ用情報を設定
                app.logger.warning(
                    "🚨 Firebase Admin SDK not available, using mock auth"
                )
                request.user_uid = "mock-user-no-firebase"
                request.user_email = "debug@example.com"
                request.user_name = "Debug User"
                app.logger.warning(f"⚠️ Using fallback mock user: {request.user_uid}")
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(
                f"🚨 Token verification failed: {e} - Token: {token[:20]}..."
            )
            app.logger.error(
                f"🚨 CRITICAL: Falling back to mock user - THIS CAUSES DATA ISOLATION FAILURE"
            )

            # 🚨 TEMPORARY FIX: 認証失敗時は即座に401を返す（データ漏洩防止）
            return (
                jsonify({"error": "Invalid or expired token", "details": str(e)}),
                401,
            )

    return decorated_function


def auth_required(f):
    """認証必須デコレータ（verify_tokenのエイリアス）"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # verify_token の機能をそのまま使用
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(" ")[1]

        # 開発用モックトークンの場合はバイパス
        if token.startswith("mock-token-for-development"):
            # 拡張されたモックトークンの場合、ユーザー情報を抽出
            if ":" in token:
                try:
                    import base64
                    import json

                    token_parts = token.split(":")
                    user_data_b64 = token_parts[1]
                    user_data = json.loads(
                        base64.b64decode(user_data_b64).decode("utf-8")
                    )
                    request.user = {
                        "uid": user_data.get("uid", "mock-user"),
                        "email": user_data.get("email", "mock@example.com"),
                        "name": user_data.get("displayName", "Mock User"),
                    }
                    request.user_uid = user_data.get("uid", "mock-user")
                    request.user_email = user_data.get("email", "mock@example.com")
                    request.user_name = user_data.get("displayName", "Mock User")
                except Exception as e:
                    app.logger.warning(f"Error parsing mock token: {e}")
                    request.user = {
                        "uid": "mock-user",
                        "email": "mock@example.com",
                        "name": "Mock User",
                    }
                    request.user_uid = "mock-user"
                    request.user_email = "mock@example.com"
                    request.user_name = "Mock User"
            else:
                request.user = {
                    "uid": "mock-user",
                    "email": "mock@example.com",
                    "name": "Mock User",
                }
                request.user_uid = "mock-user"
                request.user_email = "mock@example.com"
                request.user_name = "Mock User"
            return f(*args, **kwargs)

        try:
            # Firebase ID token verification
            if firebase_admin._apps:
                decoded_token = auth.verify_id_token(token)
                request.user = {
                    "uid": decoded_token["uid"],
                    "email": decoded_token.get("email", ""),
                    "name": decoded_token.get(
                        "name", decoded_token.get("email", "").split("@")[0]
                    ),
                }
                request.user_uid = decoded_token["uid"]
                request.user_email = decoded_token.get("email", "")
                request.user_name = decoded_token.get(
                    "name", decoded_token.get("email", "").split("@")[0]
                )
            else:
                # Firebase Admin SDKが利用できない場合はデバッグ用情報を設定
                app.logger.warning("Firebase Admin SDK not available, using mock auth")
                request.user = {
                    "uid": "mock-user-no-firebase",
                    "email": "debug@example.com",
                    "name": "Debug User",
                }
                request.user_uid = "mock-user-no-firebase"
                request.user_email = "debug@example.com"
                request.user_name = "Debug User"
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Token verification failed: {e}")
            return jsonify({"error": "Invalid authentication token"}), 401

    return decorated_function


@app.route("/")
def index():
    """メインページ"""
    import time

    timestamp = str(int(time.time()))
    return render_template("index.html", timestamp=timestamp)


@app.route("/api/health")
def health():
    """ヘルスチェック"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.1",
            "updated": "2025-08-28-profile-fix",
        }
    )


@app.route("/api/auth/verify", methods=["POST"])
@rate_limit_decorator(max_requests=30, window=3600)  # 認証は1時間に30回まで
@verify_token
def verify_auth():
    """認証検証"""
    try:
        # Firestoreが利用可能な場合のみ操作
        if db:
            # ユーザー情報をFirestoreに保存/更新
            user_ref = db.collection("users").document(request.user_uid)
            user_doc = user_ref.get()

            user_data = {
                "email": request.user_email,
                "displayName": request.user_name,
                "lastLogin": datetime.utcnow(),
            }

            if not user_doc.exists:
                # 新規ユーザー
                user_data.update(
                    {
                        "createdAt": datetime.utcnow(),
                        "storageUsed": 0,
                        "maxStorageBytes": MAX_USER_STORAGE,
                        "role": "user",
                    }
                )
                user_ref.set(user_data)
                # 新規ユーザーの個人ライブラリを初期化
                ensure_user_library(request.user_uid)
            else:
                # 既存ユーザーの最終ログイン更新
                user_ref.update({"lastLogin": datetime.utcnow()})
                user_data.update(user_doc.to_dict())

            # ログイン時に個人ライブラリを確保（既存のライブラリは保持）
            ensure_user_library(request.user_uid)

            return jsonify(
                {
                    "uid": request.user_uid,
                    "email": request.user_email,
                    "displayName": request.user_name,
                    "storageUsed": user_data.get("storageUsed", 0),
                    "maxStorageBytes": user_data.get(
                        "maxStorageBytes", MAX_USER_STORAGE
                    ),
                }
            )
        else:
            # Firestoreが利用できない場合はデフォルト値を返す
            app.logger.warning("Firestore not available, returning default values")
            return jsonify(
                {
                    "uid": request.user_uid,
                    "email": request.user_email,
                    "displayName": request.user_name,
                    "storageUsed": 0,
                    "maxStorageBytes": MAX_USER_STORAGE,
                }
            )
    except Exception as e:
        app.logger.error(f"Failed to verify auth: {e}")
        # エラーでも基本情報は返す（開発環境での動作を考慮）
        return jsonify(
            {
                "uid": request.user_uid,
                "email": request.user_email,
                "displayName": request.user_name,
                "storageUsed": 0,
                "maxStorageBytes": MAX_USER_STORAGE,
            }
        )


def extract_album_artwork(file_content):
    """MP3ファイルからアルバムアートワークを抽出"""
    try:
        # バイナリデータから一時ファイルのようなオブジェクトを作成
        file_like = io.BytesIO(file_content)

        # mutagenでファイルを読み込み
        audio_file = MutagenFile(file_like)

        if audio_file is None:
            return None

        artwork_data = None

        # ID3タグからアルバムアートを抽出（MP3）
        if hasattr(audio_file, "tags") and audio_file.tags:
            # APIC frame (Attached Picture)
            for key in audio_file.tags:
                if key.startswith("APIC"):
                    frame = audio_file.tags[key]
                    artwork_data = frame.data
                    break

        # MP4/M4A形式の場合
        elif hasattr(audio_file, "get"):
            covr = audio_file.get("covr")
            if covr and len(covr) > 0:
                artwork_data = covr[0]

        if artwork_data:
            # 画像データをPILで処理してサムネイル作成
            try:
                image = Image.open(io.BytesIO(artwork_data))
                # サムネイルサイズに縮小（最大300x300）
                image.thumbnail((300, 300), Image.Resampling.LANCZOS)

                # JPEGフォーマットでbase64エンコード
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=85)
                base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")

                return {
                    "data": f"data:image/jpeg;base64,{base64_data}",
                    "format": "image/jpeg",
                    "width": image.size[0],
                    "height": image.size[1],
                }
            except Exception as e:
                app.logger.warning(f"Failed to process artwork image: {e}")
                return None

        return None

    except Exception as e:
        app.logger.warning(f"Failed to extract album artwork: {e}")
        return None


@app.route("/api/upload/signed-url", methods=["POST"])
@verify_token
@rate_limit_decorator(
    max_requests=1000, window=3600
)  # アップロードは1時間に1000回まで（テスト用に超大幅緩和）
def create_upload_url():
    """アップロード用Signed URL生成"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    filename = data.get("filename")
    content_type = data.get("contentType", "audio/mpeg")
    file_size = data.get("fileSize", 0)

    # バリデーション
    if not filename:
        return jsonify({"error": "Filename required"}), 400

    if file_size > MAX_FILE_SIZE:
        return jsonify({"error": f"File size exceeds {MAX_FILE_SIZE} bytes"}), 400

    # 拡張子チェック
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        return (
            jsonify({"error": f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}"}),
            400,
        )

    # MIMEタイプチェック
    if content_type not in ALLOWED_MIME_TYPES:
        return (
            jsonify({"error": f"Unsupported MIME type. Allowed: {ALLOWED_MIME_TYPES}"}),
            400,
        )

    # ユーザーのストレージ使用量チェック（Firestoreが利用可能な場合のみ）
    if db is not None:
        try:
            user_doc = db.collection("users").document(request.user_uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                current_usage = user_data.get("storageUsed", 0)
                if current_usage + file_size > user_data.get(
                    "maxStorageBytes", MAX_USER_STORAGE
                ):
                    return jsonify({"error": "Storage quota exceeded"}), 413
        except Exception as e:
            app.logger.warning(f"Storage quota check failed: {e}, allowing upload")
    else:
        app.logger.info("Firestore not available, skipping storage quota check")

    # GCSオブジェクト名生成
    file_uuid = str(uuid.uuid4())
    object_name = f"users/{request.user_uid}/{file_uuid}{file_ext}"

    # Cloud Run環境では直接アップロード方式を使用
    try:
        if storage_client is None:
            app.logger.error("Storage client not available")
            return jsonify({"error": "File upload service unavailable"}), 503

        # バケットの存在確認
        bucket = storage_client.bucket(STORAGE_BUCKET)
        try:
            if not bucket.exists():
                app.logger.error(f"Storage bucket {STORAGE_BUCKET} does not exist")
                return jsonify({"error": "Storage service not configured"}), 503
        except Exception as bucket_error:
            app.logger.warning(
                f"Bucket existence check failed: {bucket_error}, proceeding anyway"
            )

        # Cloud Run環境では直接アップロード方式を推奨
        app.logger.info(f"Using direct upload for object: {object_name}")
        return jsonify(
            {
                "directUpload": True,
                "uploadEndpoint": "/api/upload/direct",
                "objectName": object_name,
                "uploadId": file_uuid,
                "contentType": content_type,
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to generate signed URL: {e}")
        return jsonify({"error": "Failed to generate upload URL"}), 500


@app.route("/api/tracks", methods=["POST"])
@verify_token
@rate_limit_decorator(
    max_requests=1000, window=3600
)  # トラック作成は1時間に1000回まで（テスト用に超大幅緩和）
def create_track():
    """トラック作成"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    # 入力値検証の強化
    try:
        # タイトルの検証
        title = validate_string_input(
            data.get("title"), "タイトル", min_length=1, max_length=200
        )

        # ファイル名の検証
        original_filename = validate_filename(data.get("originalFilename"))

        # 説明文の検証（オプション）
        description = validate_string_input(
            data.get("description"),
            "説明",
            min_length=0,
            max_length=1000,
            allow_empty=True,
        )

        # ファイルサイズの検証
        file_size = validate_positive_integer(
            data.get("sizeBytes"), "ファイルサイズ", max_value=MAX_FILE_SIZE
        )

        # GCSパスの検証
        gcs_path = validate_string_input(
            data.get("gcsPath"), "ファイルパス", min_length=1, max_length=500
        )

        # GCSパスの危険な文字チェック
        if ".." in gcs_path or gcs_path.startswith("/"):
            raise ValueError("ファイルパスに不正な内容が含まれています")

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    # GCSオブジェクトの存在確認（Storage Clientが利用可能な場合のみ）
    if storage_client is not None:
        try:
            bucket = storage_client.bucket(STORAGE_BUCKET)
            blob = bucket.blob(gcs_path)
            if not blob.exists():
                return jsonify({"error": "File not found in storage"}), 404
        except Exception as e:
            app.logger.error(f"Failed to verify file existence: {e}")
            return jsonify({"error": "Failed to verify file"}), 500
    else:
        app.logger.warning(
            "Storage client not available, skipping file existence check"
        )

    # トラックドキュメント作成
    track_id = str(uuid.uuid4())
    track_data = {
        "title": title,
        "description": description,
        "uploaderUid": request.user_uid,
        "uploaderName": request.user_name,
        "gcsPath": gcs_path,
        "originalFilename": original_filename,
        "durationSec": data.get("durationSec", 0),
        "sizeBytes": file_size,
        "contentType": data.get("contentType", "audio/mpeg"),
        "status": "approved",  # 簡単のため自動承認
        "visibility": data.get("visibility", "public"),  # デフォルトをpublicに変更
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
        "playCount": 0,
        "tags": data.get("tags", []),
        "artwork": data.get("artwork"),  # アルバムアートワークのbase64データ
    }

    try:
        # Firestoreに保存（利用可能な場合のみ）
        if db is not None:
            try:
                db.collection("tracks").document(track_id).set(track_data)

                # ユーザーのストレージ使用量更新
                user_ref = db.collection("users").document(request.user_uid)
                user_ref.update({"storageUsed": firestore.Increment(data["sizeBytes"])})

                app.logger.info(f"Track created successfully in Firestore: {track_id}")
                return (
                    jsonify(
                        {"trackId": track_id, "message": "Track created successfully"}
                    ),
                    201,
                )

            except Exception as firestore_error:
                # Firestoreエラーの場合はログに記録してフォールバック
                app.logger.warning(
                    f"Firestore operation failed, falling back to file-only upload: {firestore_error}"
                )
                return (
                    jsonify(
                        {
                            "trackId": track_id,
                            "message": "File uploaded successfully (metadata not saved - Firestore error)",
                        }
                    ),
                    201,
                )
        else:
            # Firestoreが利用できない場合はファイルのアップロードのみ成功とする
            app.logger.info(
                "Firestore not available, track metadata not saved but file upload successful"
            )
            return (
                jsonify(
                    {
                        "trackId": track_id,
                        "message": "File uploaded successfully (metadata not saved - Firestore unavailable)",
                    }
                ),
                201,
            )

    except Exception as e:
        app.logger.error(f"Failed to create track: {e}")
        return jsonify({"error": "Failed to create track"}), 500


@app.route("/api/upload/direct", methods=["POST"])
@verify_token
def direct_upload():
    """直接アップロード（Signed URL生成が失敗した場合の代替手段）"""
    try:
        # フォームデータからファイルを取得
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # 追加パラメータ
        object_name = request.form.get("objectName")
        upload_id = request.form.get("uploadId")

        if not object_name or not upload_id:
            return jsonify({"error": "Missing upload parameters"}), 400

        # ファイルサイズ制限
        file.seek(0, 2)  # ファイル末尾に移動
        file_size = file.tell()
        file.seek(0)  # 先頭に戻る

        if file_size > MAX_FILE_SIZE:
            return jsonify({"error": f"File size exceeds {MAX_FILE_SIZE} bytes"}), 400

        # GCSに直接アップロード
        if storage_client is None:
            app.logger.error(
                f"Storage client not initialized. STORAGE_BUCKET: {STORAGE_BUCKET}"
            )
            return (
                jsonify(
                    {
                        "error": "Storage service unavailable",
                        "details": "Google Cloud Storage client is not initialized",
                        "bucket": STORAGE_BUCKET,
                    }
                ),
                503,
            )

        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(object_name)

        # ファイルをアップロード
        blob.upload_from_file(file, content_type=file.content_type or "audio/mpeg")

        app.logger.info(f"Direct upload successful: {object_name}")

        return jsonify(
            {
                "success": True,
                "objectName": object_name,
                "uploadId": upload_id,
                "message": "File uploaded successfully",
            }
        )

    except Exception as e:
        error_msg = f"Direct upload failed: {str(e)}"
        app.logger.error(error_msg)
        return (
            jsonify(
                {"error": "Upload failed", "details": str(e), "type": type(e).__name__}
            ),
            500,
        )


@app.route("/api/extract-artwork", methods=["POST"])
@verify_token
def extract_artwork():
    """アップロード前にクライアントからアルバムアートワークを抽出"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]

        if not file or file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # ファイル内容を読み取り
        file_content = file.read()
        file.seek(0)  # ファイルポインタをリセット

        # 音声ファイルのみ処理
        if not file.content_type or not file.content_type.startswith("audio/"):
            return jsonify({"artwork": None})

        # アルバムアートワークを抽出
        artwork_info = extract_album_artwork(file_content)

        return jsonify({"success": True, "artwork": artwork_info})

    except Exception as e:
        app.logger.error(f"Failed to extract artwork: {e}")
        return jsonify({"success": False, "artwork": None, "error": str(e)}), 500


@app.route("/api/tracks", methods=["GET"])
@verify_token
def list_tracks():
    """トラック一覧取得"""
    try:
        # ログインユーザーのUID取得
        current_user_uid = request.user_uid

        # クエリパラメータ
        limit = min(int(request.args.get("limit", 20)), 100)
        visibility = request.args.get(
            "visibility", "private"
        )  # デフォルトをprivateに変更（ユーザー自身のトラックのみ）
        search = request.args.get("search", "")
        user_uid = request.args.get(
            "userId", current_user_uid
        )  # デフォルトで現在のユーザー

        app.logger.info(
            f"🔍 Tracks request: current_user_uid={current_user_uid}, user_uid={user_uid}, limit={limit}, visibility={visibility}, search='{search}', db={db is not None}"
        )

        # 🚨 重要：ユーザー認証の検証ログ
        if current_user_uid != user_uid:
            app.logger.warning(
                f"⚠️ User UID mismatch! current_user_uid={current_user_uid} != user_uid={user_uid}"
            )
        else:
            app.logger.info(f"✅ User UID match confirmed: {current_user_uid}")

        # Firestoreが利用できない場合はデモデータを返す
        if db is None:
            app.logger.info(
                "Firestore not available, returning empty tracks array for user: "
                + current_user_uid
            )
            return jsonify({"tracks": []})

        # Firestoreクエリ構築（ユーザー別フィルタリング）
        try:
            if visibility == "public":
                # パブリックの場合：承認済み全トラック
                app.logger.info(
                    f"📊 Building PUBLIC query: visibility='public', status='approved', limit={limit * 2}"
                )
                query = (
                    db.collection("tracks")
                    .where("visibility", "==", "public")
                    .where("status", "==", "approved")
                    .limit(limit * 2)
                )
            else:
                # プライベートの場合：指定されたユーザーのトラックのみ
                app.logger.info(
                    f"🔒 Building PRIVATE query: uploaderUid='{user_uid}', limit={limit * 2}"
                )
                query = (
                    db.collection("tracks")
                    .where("uploaderUid", "==", user_uid)
                    .limit(limit * 2)
                )

            app.logger.info("🔍 Executing Firestore query...")
            docs = query.stream()
            app.logger.info("✅ Firestore query executed successfully")
        except Exception as e:
            app.logger.warning(
                f"Firestore query failed, returning empty tracks array: {e}"
            )
            # Firestoreエラー時も空の配列を返す（新規ユーザーに配慮）
            return jsonify({"tracks": []})

        tracks = []
        track_count = 0
        for doc in docs:
            try:
                track_data = doc.to_dict()
                if not track_data:
                    continue

                track_count += 1
                track_data["trackId"] = doc.id

                # 🔍 デバッグ：取得したトラックの詳細をログ出力
                uploader_uid = track_data.get("uploaderUid", "MISSING")
                track_title = track_data.get("title", "Untitled")
                track_visibility = track_data.get("visibility", "MISSING")
                app.logger.info(
                    f"📀 Track {track_count}: ID={doc.id[:8]}..., title='{track_title}', uploaderUid='{uploader_uid}', visibility='{track_visibility}'"
                )

                # フィルタリングはデータベースレベルで実行済み

                # 検索フィルタ（簡易）
                if search:
                    searchable_text = f"{track_data.get('title', '')} {track_data.get('description', '')} {' '.join(track_data.get('tags', []))}".lower()
                    if search.lower() not in searchable_text:
                        continue

                # createdAtをISO文字列に変換
                if "createdAt" in track_data and track_data["createdAt"]:
                    try:
                        track_data["createdAt"] = track_data["createdAt"].isoformat()
                    except:
                        track_data["createdAt"] = str(track_data["createdAt"])
                if "updatedAt" in track_data and track_data["updatedAt"]:
                    try:
                        track_data["updatedAt"] = track_data["updatedAt"].isoformat()
                    except:
                        track_data["updatedAt"] = str(track_data["updatedAt"])

                tracks.append(track_data)

                # 制限に達したら終了
                if len(tracks) >= limit:
                    break

            except Exception as e:
                app.logger.warning(f"Error processing track doc: {e}")
                continue

        app.logger.info(
            f"📊 Query Summary: current_user={current_user_uid}, visibility={visibility}, returned {len(tracks)} tracks (processed {track_count} from Firestore)"
        )

        # 🚨 重要：すべてのユーザーに同じトラックが返されているかチェック
        if tracks:
            unique_uploaders = set(
                track.get("uploaderUid", "MISSING") for track in tracks
            )
            app.logger.info(
                f"🔍 Unique uploaderUids in response: {list(unique_uploaders)}"
            )
            if len(unique_uploaders) > 1 and visibility == "private":
                app.logger.error(
                    f"🚨 CRITICAL: Multiple uploaderUids found in private mode! Expected only: {user_uid}"
                )

        return jsonify({"tracks": tracks})

    except Exception as e:
        app.logger.error(f"Unexpected error in list_tracks: {e}")
        # 最終フォールバック - 空の配列を返す（サンプルトラックは返さない）
        app.logger.info("Returning empty tracks array due to unexpected error")
        return jsonify({"tracks": []})


@app.route("/api/tracks/<track_id>/play-url", methods=["GET"])
def get_play_url(track_id):
    """再生用Signed URL生成"""
    try:
        # トラック取得（Firestoreが利用可能な場合のみ）
        if db is None:
            return (
                jsonify(
                    {"error": "Track playback unavailable (database not configured)"}
                ),
                503,
            )

        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # 可視性チェック
        if track_data.get("visibility") != "public":
            # プライベートトラックの場合、所有者チェックが必要
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    decoded_token = auth.verify_id_token(token)
                    if decoded_token["uid"] != track_data.get("uploaderUid"):
                        return jsonify({"error": "Access denied"}), 403
                except:
                    return jsonify({"error": "Access denied"}), 403
            else:
                return jsonify({"error": "Access denied"}), 403

        # Storage Client利用可能性チェック
        if storage_client is None:
            return jsonify({"error": "File playback service unavailable"}), 503

        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(track_data["gcsPath"])

        # Signed URL生成を試行
        try:
            play_url = blob.generate_signed_url(
                version="v4", expiration=timedelta(minutes=10), method="GET"
            )

            # 再生回数更新（Firestoreが利用可能な場合のみ）
            try:
                db.collection("tracks").document(track_id).update(
                    {"playCount": firestore.Increment(1)}
                )
            except Exception as e:
                app.logger.warning(f"Failed to update play count: {e}")

            return jsonify(
                {
                    "playUrl": play_url,
                    "track": {
                        "trackId": track_id,
                        "title": track_data.get("title"),
                        "uploaderName": track_data.get("uploaderName"),
                        "durationSec": track_data.get("durationSec", 0),
                    },
                }
            )

        except Exception as signed_error:
            app.logger.warning(
                f"Signed URL generation failed for playback, using proxy stream: {signed_error}"
            )

            # フォールバック: プロキシストリーミングエンドポイントを使用
            proxy_url = f"/api/tracks/{track_id}/stream"

            # 再生回数更新（フォールバック時も実行）
            try:
                db.collection("tracks").document(track_id).update(
                    {"playCount": firestore.Increment(1)}
                )
            except Exception as e:
                app.logger.warning(f"Failed to update play count: {e}")

            return jsonify(
                {
                    "playUrl": proxy_url,
                    "proxyStream": True,
                    "track": {
                        "trackId": track_id,
                        "title": track_data.get("title"),
                        "uploaderName": track_data.get("uploaderName"),
                        "durationSec": track_data.get("durationSec", 0),
                    },
                }
            )

    except Exception as e:
        app.logger.error(f"Failed to generate play URL: {e}")
        return jsonify({"error": "Failed to generate play URL"}), 500


@app.route("/api/tracks/<track_id>/stream")
def stream_track(track_id):
    """プロキシストリーミング（Signed URL生成が失敗した場合の代替手段）"""
    try:
        # トラック取得（Firestoreが利用可能な場合のみ）
        if db is None:
            return (
                jsonify(
                    {"error": "Track streaming unavailable (database not configured)"}
                ),
                503,
            )

        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # 可視性チェック（パブリックトラックのみストリーミング）
        if track_data.get("visibility") != "public":
            return jsonify({"error": "Access denied"}), 403

        # Storage Client利用可能性チェック
        if storage_client is None:
            return jsonify({"error": "File streaming service unavailable"}), 503

        bucket = storage_client.bucket(STORAGE_BUCKET)
        blob = bucket.blob(track_data["gcsPath"])

        # ファイル存在確認
        if not blob.exists():
            return jsonify({"error": "Audio file not found"}), 404

        # ファイルをダウンロードしてストリーミング
        from flask import Response, stream_with_context

        def generate():
            try:
                # より効率的なストリーミング（メモリ消費を抑制）
                chunk_size = 64 * 1024  # 64KB chunk

                # blobのサイズを取得
                blob.reload()
                total_size = blob.size

                # 範囲ダウンロードでストリーミング
                start = 0
                while start < total_size:
                    end = min(start + chunk_size - 1, total_size - 1)
                    chunk = blob.download_as_bytes(start=start, end=end)
                    yield chunk
                    start = end + 1

            except Exception as e:
                app.logger.error(f"Error streaming track: {e}")
                yield b""

        # HTTPヘッダー用に安全なファイル名を生成
        original_filename = track_data.get("originalFilename", "audio.mp3")
        safe_filename = (
            original_filename.encode("ascii", "ignore").decode("ascii") or "audio.mp3"
        )

        # ファイルサイズを取得
        blob.reload()
        file_size = blob.size

        return Response(
            stream_with_context(generate()),
            mimetype=track_data.get("contentType", "audio/mpeg"),
            headers={
                "Content-Disposition": f'inline; filename="{safe_filename}"',
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
            },
        )

    except Exception as e:
        app.logger.error(f"Failed to stream track: {e}")
        return jsonify({"error": "Failed to stream track"}), 500


@app.route("/api/tracks/<track_id>", methods=["GET"])
@verify_token
def get_track(track_id):
    """個別トラック取得（編集用）"""
    try:
        if db is None:
            return (
                jsonify({"error": "Track data unavailable (database not configured)"}),
                503,
            )

        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # 権限チェック：自分のトラックのみ詳細情報を取得可能
        user_uid = request.user_uid
        if track_data.get("uploaderUid") != user_uid:
            return (
                jsonify({"error": "Access denied. You can only edit your own tracks."}),
                403,
            )

        # 編集用に必要な情報を返す
        return jsonify(
            {
                "trackId": track_id,
                "title": track_data.get("title", ""),
                "description": track_data.get("description", ""),
                "genre": track_data.get("genre", ""),
                "tags": track_data.get("tags", ""),
                "isPublic": track_data.get("visibility", "public") == "public",
                "allowDownloads": track_data.get("allowDownloads", False),
                "uploaderUid": track_data.get("uploaderUid"),
                "createdAt": track_data.get("createdAt"),
                "updatedAt": track_data.get("updatedAt"),
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to get track {track_id}: {e}")
        return jsonify({"error": "Failed to retrieve track data"}), 500


@app.route("/api/tracks/<track_id>", methods=["PUT"])
@verify_token
def update_track(track_id):
    """トラック情報更新"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Track update unavailable (database not configured)"}
                ),
                503,
            )

        # リクエストデータ取得
        try:
            data = request.get_json(force=True)
        except Exception as json_error:
            app.logger.error(f"JSON parsing error: {json_error}")
            app.logger.error(f"Raw request data: {request.data}")
            return jsonify({"error": "Invalid JSON in request body"}), 400

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # トラック存在確認と権限チェック
        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()
        user_uid = request.user_uid

        if track_data.get("uploaderUid") != user_uid:
            return (
                jsonify({"error": "Access denied. You can only edit your own tracks."}),
                403,
            )

        # 更新データの準備
        update_data = {}

        # タイトル（必須）
        title = data.get("title")
        if title is not None:
            title = title.strip()
        else:
            title = ""
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if len(title) > 200:
            return jsonify({"error": "Title must be 200 characters or less"}), 400
        update_data["title"] = title

        # 説明（オプション）
        description = data.get("description")
        if description is not None:
            description = description.strip()
        else:
            description = ""
        if description and len(description) > 1000:
            return (
                jsonify({"error": "Description must be 1000 characters or less"}),
                400,
            )
        update_data["description"] = description or None

        # ジャンル（オプション）
        genre = data.get("genre")
        if genre is not None:
            genre = genre.strip()
        else:
            genre = ""
        if genre:
            valid_genres = [
                "technology",
                "business",
                "education",
                "entertainment",
                "news",
                "health",
                "arts",
                "sports",
                "science",
                "music",
                "comedy",
                "other",
            ]
            if genre not in valid_genres:
                return (
                    jsonify(
                        {
                            "error": f'Invalid genre. Must be one of: {", ".join(valid_genres)}'
                        }
                    ),
                    400,
                )
        update_data["genre"] = genre or None

        # タグ（オプション）
        tags = data.get("tags")
        if tags is not None:
            tags = tags.strip()
        else:
            tags = ""
        if tags and len(tags) > 200:
            return jsonify({"error": "Tags must be 200 characters or less"}), 400
        update_data["tags"] = tags or None

        # 可視性設定
        is_public = data.get("isPublic", True)
        update_data["visibility"] = "public" if is_public else "private"

        # ダウンロード許可設定
        allow_downloads = data.get("allowDownloads", False)
        update_data["allowDownloads"] = allow_downloads

        # 更新日時
        update_data["updatedAt"] = datetime.utcnow()

        # Firestoreに更新
        app.logger.info(
            f"🔄 Attempting to update track {track_id} with data: {update_data}"
        )

        try:
            db.collection("tracks").document(track_id).update(update_data)
        except Exception as firestore_error:
            app.logger.error(f"Firestore update error: {firestore_error}")
            return (
                jsonify({"error": f"Database update failed: {str(firestore_error)}"}),
                500,
            )

        app.logger.info(f"✅ Track {track_id} updated successfully by user {user_uid}")

        return jsonify(
            {
                "message": "Track updated successfully",
                "trackId": track_id,
                "updatedFields": list(update_data.keys()),
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to update track {track_id}: {e}")
        import traceback

        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({"error": f"Failed to update track: {str(e)}"}), 500


@app.route("/api/tracks/<track_id>", methods=["DELETE"])
@verify_token
@rate_limit_decorator(
    max_requests=1000, window=3600
)  # 削除は1時間に1000回まで（テスト用に超大幅緩和）
def delete_track(track_id):
    """トラック削除"""
    try:
        # トラック取得と権限確認
        if db is None:
            return (
                jsonify(
                    {"error": "Track deletion unavailable (database not configured)"}
                ),
                503,
            )

        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # 所有者チェック
        if track_data.get("uploaderUid") != request.user_uid:
            return (
                jsonify(
                    {"error": "Permission denied - you can only delete your own tracks"}
                ),
                403,
            )

        # GCSファイル削除
        if storage_client is not None:
            try:
                bucket = storage_client.bucket(STORAGE_BUCKET)
                blob = bucket.blob(track_data["gcsPath"])
                if blob.exists():
                    blob.delete()
                    app.logger.info(f"Deleted GCS file: {track_data['gcsPath']}")
                else:
                    app.logger.warning(
                        f"GCS file not found for deletion: {track_data['gcsPath']}"
                    )
            except Exception as e:
                app.logger.error(f"Failed to delete GCS file: {e}")
                # GCS削除に失敗してもFirestoreは削除を続行
        else:
            app.logger.warning(
                "Storage client not available, skipping GCS file deletion"
            )

        # Firestoreドキュメント削除
        try:
            track_doc.reference.delete()
            app.logger.info(f"Deleted Firestore document: {track_id}")
        except Exception as e:
            app.logger.error(f"Failed to delete Firestore document: {e}")
            return jsonify({"error": "Failed to delete track metadata"}), 500

        # ユーザーのストレージ使用量更新
        try:
            user_ref = db.collection("users").document(request.user_uid)
            user_ref.update(
                {"storageUsed": firestore.Increment(-track_data.get("sizeBytes", 0))}
            )
        except Exception as e:
            app.logger.warning(f"Failed to update user storage: {e}")

        # user_librariesからもトラック参照を削除
        try:
            user_library_ref = db.collection("user_libraries").document(
                request.user_uid
            )
            user_library_doc = user_library_ref.get()
            if user_library_doc.exists:
                user_library_data = user_library_doc.to_dict()
                saved_tracks = user_library_data.get("savedTracks", [])
                if track_id in saved_tracks:
                    saved_tracks.remove(track_id)
                    user_library_ref.update({"savedTracks": saved_tracks})
                    app.logger.info(f"Removed track {track_id} from user library")
        except Exception as e:
            app.logger.warning(f"Failed to update user library: {e}")

        return jsonify({"message": "Track deleted successfully", "trackId": track_id})

    except Exception as e:
        app.logger.error(f"Failed to delete track: {e}")
        return jsonify({"error": "Failed to delete track"}), 500


@app.route("/api/tracks/<track_id>/delete-orphaned-force", methods=["DELETE"])
def delete_orphaned_track_force(track_id):
    """一時的な強制削除エンドポイント（認証なし）"""
    return delete_orphaned_track_impl(track_id)


@app.route("/api/tracks/<track_id>/delete-orphaned", methods=["DELETE"])
@verify_token
@rate_limit_decorator(
    max_requests=100, window=3600
)  # 破損トラック削除は1時間に100回まで
def delete_orphaned_track(track_id):
    return delete_orphaned_track_impl(track_id)


def delete_orphaned_track_impl(track_id):
    """破損トラック削除（アカウントに紐づいていない、音声ファイルがないトラック）"""
    try:
        app.logger.info(f"Starting orphaned track deletion for track_id: {track_id}")

        # トラック取得
        if db is None:
            app.logger.error(f"Database not configured for track deletion: {track_id}")
            return (
                jsonify(
                    {"error": "Track deletion unavailable (database not configured)"}
                ),
                503,
            )

        track_doc = db.collection("tracks").document(track_id).get()
        track_exists_in_firestore = track_doc.exists

        if track_exists_in_firestore:
            track_data = track_doc.to_dict()

            # 破損トラックの条件をチェック（ポッドキャストエピソードの場合は条件を緩和）
            is_podcast = (
                track_data.get("isPodcast") or track_data.get("type") == "podcast"
            )

            if is_podcast:
                # ポッドキャストエピソードの場合は、audioUrlがない場合のみ破損とみなす
                is_orphaned = not track_data.get("audioUrl") and not track_data.get(
                    "audio_url"
                )
                app.logger.info(
                    f"Podcast episode {track_id} orphaned check: audioUrl={bool(track_data.get('audioUrl'))}, audio_url={bool(track_data.get('audio_url'))}"
                )
            else:
                # 通常トラックの場合は従来の条件
                is_orphaned = (
                    not track_data.get("uploaderUid")  # アカウントに紐づいていない
                    or not track_data.get("audioUrl")  # 音声URLがない
                    or not track_data.get("gcsPath")  # GCSパスがない
                )

            if not is_orphaned:
                app.logger.warning(
                    f"Track {track_id} is not orphaned - isPodcast: {is_podcast}, uploaderUid: {track_data.get('uploaderUid')}, audioUrl: {bool(track_data.get('audioUrl'))}, gcsPath: {bool(track_data.get('gcsPath'))}"
                )
                # ポッドキャストの場合でも一時的に削除を許可（テスト用）
                if is_podcast:
                    app.logger.info(
                        f"Allowing deletion of podcast episode {track_id} for cleanup purposes"
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "This track is not orphaned and cannot be deleted using this endpoint"
                            }
                        ),
                        400,
                    )

            app.logger.info(
                f"Deleting orphaned track: {track_id}, conditions: uploaderUid={track_data.get('uploaderUid')}, audioUrl={bool(track_data.get('audioUrl'))}, gcsPath={bool(track_data.get('gcsPath'))}"
            )

            # GCSファイル削除（存在する場合のみ）
            if storage_client is not None and track_data.get("gcsPath"):
                try:
                    bucket = storage_client.bucket(STORAGE_BUCKET)
                    blob = bucket.blob(track_data["gcsPath"])
                    if blob.exists():
                        blob.delete()
                        app.logger.info(
                            f"Deleted GCS file for orphaned track: {track_data['gcsPath']}"
                        )
                    else:
                        app.logger.info(
                            f"GCS file not found for orphaned track: {track_data['gcsPath']}"
                        )
                except Exception as e:
                    app.logger.warning(
                        f"Failed to delete GCS file for orphaned track: {e}"
                    )
                    # GCS削除に失敗してもFirestoreは削除を続行

            # Firestoreドキュメント削除
            try:
                track_doc.reference.delete()
                app.logger.info(f"Deleted orphaned Firestore document: {track_id}")
            except Exception as e:
                app.logger.error(f"Failed to delete orphaned Firestore document: {e}")
                return (
                    jsonify({"error": "Failed to delete orphaned track metadata"}),
                    500,
                )
        else:
            # トラックがFirestoreに存在しない場合は、プレイリストとライブラリからのみ削除
            app.logger.info(
                f"Track {track_id} not found in Firestore but will be removed from playlists and libraries"
            )
            track_data = {}  # 空のデータとして処理

        # プレイリストからも削除（全てのプレイリストから削除）
        try:
            # 通常のtracks配列から削除
            playlists = (
                db.collection("playlists")
                .where("tracks", "array_contains", track_id)
                .get()
            )
            for playlist_doc in playlists:
                playlist_ref = playlist_doc.reference
                playlist_data = playlist_doc.to_dict()
                tracks = playlist_data.get("tracks", [])
                if track_id in tracks:
                    tracks.remove(track_id)
                    playlist_ref.update(
                        {
                            "tracks": tracks,
                            "trackCount": len(tracks),
                            "updatedAt": datetime.utcnow(),
                        }
                    )
                    app.logger.info(
                        f"Removed orphaned track {track_id} from playlist {playlist_doc.id}"
                    )

            # podcastEpisodes配列からも削除
            all_playlists = db.collection("playlists").get()
            for playlist_doc in all_playlists:
                playlist_ref = playlist_doc.reference
                playlist_data = playlist_doc.to_dict()
                podcast_episodes = playlist_data.get("podcastEpisodes", [])

                # episodeIdがtrack_idと一致するエピソードを探して削除
                updated_episodes = []
                removed_count = 0
                for episode in podcast_episodes:
                    if episode.get("episodeId") != track_id:
                        updated_episodes.append(episode)
                    else:
                        removed_count += 1
                        app.logger.info(
                            f"Found orphaned podcast episode to remove: {episode.get('title')} (ID: {track_id})"
                        )

                # エピソードが削除された場合のみプレイリストを更新
                if removed_count > 0:
                    tracks = playlist_data.get("tracks", [])
                    total_track_count = len(tracks) + len(updated_episodes)
                    playlist_ref.update(
                        {
                            "podcastEpisodes": updated_episodes,
                            "trackCount": total_track_count,
                            "updatedAt": datetime.utcnow(),
                        }
                    )
                    app.logger.info(
                        f"Removed {removed_count} orphaned podcast episode(s) {track_id} from playlist {playlist_doc.id}"
                    )

        except Exception as e:
            app.logger.warning(f"Failed to remove orphaned track from playlists: {e}")

        # ユーザーライブラリからも削除（全てのユーザーから削除）
        try:
            user_libraries = (
                db.collection("user_libraries")
                .where("savedTracks", "array_contains", track_id)
                .get()
            )
            for user_library_doc in user_libraries:
                user_library_ref = user_library_doc.reference
                user_library_data = user_library_doc.to_dict()
                saved_tracks = user_library_data.get("savedTracks", [])
                if track_id in saved_tracks:
                    saved_tracks.remove(track_id)
                    user_library_ref.update({"savedTracks": saved_tracks})
                    app.logger.info(
                        f"Removed orphaned track {track_id} from user library {user_library_doc.id}"
                    )
        except Exception as e:
            app.logger.warning(
                f"Failed to remove orphaned track from user libraries: {e}"
            )

        return jsonify(
            {"message": "Orphaned track deleted successfully", "trackId": track_id}
        )

    except Exception as e:
        app.logger.error(f"Failed to delete orphaned track: {e}")
        return jsonify({"error": "Failed to delete orphaned track"}), 500


@app.route("/api/tracks/<track_id>/remove-from-library", methods=["DELETE"])
@verify_token
def remove_from_library(track_id):
    """個人ライブラリからトラック削除"""
    app.logger.info(
        f"🔍 Remove from library request: track_id={track_id}, user_uid={request.user_uid}"
    )
    try:
        # Firestoreが利用可能かチェック
        if db is None:
            app.logger.info(
                f"🔧 Firestore not available, using demo mode for track deletion: {track_id}"
            )

            # デモ環境での削除処理（メモリベース）
            demo_track_ids = ["demo-1", "demo-2", "user-track-1", "user-track-2"]

            if track_id not in demo_track_ids:
                return jsonify({"error": "Track not found in demo data"}), 404

            # デモ環境では常に削除成功を返す（実際のデータ削除は行わない）
            app.logger.info(
                f"✅ Demo mode: Successfully 'removed' track {track_id} from library"
            )

            return jsonify(
                {
                    "message": "Track removed from your library successfully (demo mode)",
                    "trackId": track_id,
                    "trackTitle": f"Demo Track {track_id}",
                    "demoMode": True,
                }
            )

        # トラックの存在確認
        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # 自分のトラックの場合は完全削除を推奨
        app.logger.info(
            f"🔍 Owner check: track.uploaderUid='{track_data.get('uploaderUid')}' vs request.user_uid='{request.user_uid}'"
        )
        if track_data.get("uploaderUid") == request.user_uid:
            app.logger.info(
                f"✅ Owner match detected, returning 400 with permanent_delete message"
            )
            return (
                jsonify(
                    {
                        "error": "Use DELETE /api/tracks/{track_id} to permanently delete your own tracks",
                        "recommendation": "permanent_delete",
                    }
                ),
                400,
            )
        else:
            app.logger.info(
                f"ℹ️ Not owner, proceeding to library removal. Track owner: '{track_data.get('uploaderUid')}'"
            )

        # ユーザーのライブラリ記録から削除
        try:
            user_library_ref = db.collection("user_libraries").document(
                request.user_uid
            )
            user_library_doc = user_library_ref.get()

            if user_library_doc.exists:
                library_data = user_library_doc.to_dict()
                saved_tracks = library_data.get("savedTracks", [])

                # トラックIDがライブラリに存在するかチェック
                if track_id in saved_tracks:
                    # ライブラリから削除
                    saved_tracks.remove(track_id)
                    user_library_ref.update(
                        {"savedTracks": saved_tracks, "updatedAt": datetime.utcnow()}
                    )
                    app.logger.info(
                        f"Removed track {track_id} from user {request.user_uid} library"
                    )
                else:
                    return jsonify({"error": "Track not found in your library"}), 404
            else:
                # ライブラリが存在しない場合は自動初期化
                app.logger.info(
                    f"Personal library not found for user {request.user_uid}, initializing..."
                )
                if ensure_user_library(request.user_uid):
                    # 初期化後は空のライブラリなので、トラックは存在しない
                    return (
                        jsonify(
                            {
                                "error": "Track not found in your library (library was just initialized)"
                            }
                        ),
                        404,
                    )
                else:
                    return (
                        jsonify(
                            {
                                "error": "Personal library not found and failed to initialize"
                            }
                        ),
                        500,
                    )

            return jsonify(
                {
                    "message": "Track removed from your library successfully",
                    "trackId": track_id,
                    "trackTitle": track_data.get("title", "Unknown Track"),
                }
            )

        except Exception as e:
            app.logger.error(f"Failed to remove from library: {e}")
            return jsonify({"error": "Failed to remove from library"}), 500

    except Exception as e:
        app.logger.error(f"Failed to remove track from library: {e}")
        return jsonify({"error": "Failed to remove track from library"}), 500


@app.route("/api/tracks/<track_id>/add-to-library", methods=["POST"])
@verify_token
def add_to_library(track_id):
    """個人ライブラリにトラック追加"""
    try:
        # Firestoreが利用可能かチェック
        if db is None:
            app.logger.info(
                f"🔧 Firestore not available, using demo mode for track addition: {track_id}"
            )

            # デモ環境での追加処理（メモリベース）
            demo_track_ids = ["demo-1", "demo-2", "user-track-1", "user-track-2"]

            if track_id not in demo_track_ids:
                return jsonify({"error": "Track not found in demo data"}), 404

            # デモ環境では常に追加成功を返す（実際のデータ追加は行わない）
            app.logger.info(
                f"✅ Demo mode: Successfully 'added' track {track_id} to library"
            )

            return jsonify(
                {
                    "message": "Track added to your library successfully (demo mode)",
                    "trackId": track_id,
                    "trackTitle": f"Demo Track {track_id}",
                    "demoMode": True,
                }
            )

        # トラックの存在確認
        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        track_data = track_doc.to_dict()

        # パブリックトラックのみライブラリ追加可能
        if track_data.get("visibility") != "public":
            return jsonify({"error": "Only public tracks can be added to library"}), 403

        # ユーザーのライブラリに追加
        try:
            user_library_ref = db.collection("user_libraries").document(
                request.user_uid
            )
            user_library_doc = user_library_ref.get()

            if user_library_doc.exists:
                library_data = user_library_doc.to_dict()
                saved_tracks = library_data.get("savedTracks", [])

                # 既に追加済みかチェック
                if track_id not in saved_tracks:
                    saved_tracks.append(track_id)
                    user_library_ref.update(
                        {"savedTracks": saved_tracks, "updatedAt": datetime.utcnow()}
                    )
                    app.logger.info(
                        f"Added track {track_id} to user {request.user_uid} library"
                    )
                else:
                    return jsonify({"message": "Track already in your library"}), 200
            else:
                # 新規ライブラリ作成
                user_library_ref.set(
                    {
                        "userId": request.user_uid,
                        "savedTracks": [track_id],
                        "createdAt": datetime.utcnow(),
                        "updatedAt": datetime.utcnow(),
                    }
                )
                app.logger.info(
                    f"Created library and added track {track_id} for user {request.user_uid}"
                )

            return jsonify(
                {
                    "message": "Track added to your library successfully",
                    "trackId": track_id,
                    "trackTitle": track_data.get("title", "Unknown Track"),
                }
            )

        except Exception as e:
            app.logger.error(f"Failed to add to library: {e}")
            return jsonify({"error": "Failed to add to library"}), 500

    except Exception as e:
        app.logger.error(f"Failed to add track to library: {e}")
        return jsonify({"error": "Failed to add track to library"}), 500


# User Search and Profile Endpoints
@app.route("/api/users/search", methods=["GET"])
def search_users():
    """実際のFirestoreユーザー検索"""
    try:
        query = request.args.get("q", "").strip().lower()

        if not query:
            return jsonify({"users": []})

        # Firestoreの'user_profiles'コレクションから実際のユーザーを検索
        users_ref = db.collection("user_profiles")
        all_users_docs = users_ref.stream()

        filtered_users = []

        for user_doc in all_users_docs:
            user_data = user_doc.to_dict()
            user_id = user_doc.id

            # 検索クエリがユーザーの表示名、メール、プロフィール説明に含まれているかチェック
            display_name = user_data.get("displayName", "").lower()
            email = user_data.get("email", "").lower()
            bio = user_data.get("bio", "").lower()

            if query in display_name or query in email or query in bio:

                # そのユーザーのトラック数と総時間を計算
                user_tracks = (
                    db.collection("tracks").where("uploaderUid", "==", user_id).stream()
                )
                track_count = 0
                total_duration = 0

                for track in user_tracks:
                    track_data = track.to_dict()
                    track_count += 1
                    total_duration += track_data.get("durationSec", 0)

                filtered_users.append(
                    {
                        "userId": user_id,
                        "displayName": user_data.get("displayName", "Unknown User"),
                        "email": user_data.get("email", ""),
                        "bio": user_data.get("bio", ""),
                        "trackCount": track_count,
                        "totalDurationMinutes": total_duration // 60,
                        "followersCount": user_data.get("followersCount", 0),
                        "avatarUrl": user_data.get("avatarUrl", ""),
                        "joinedDate": (
                            user_data.get("createdAt", datetime.utcnow()).strftime(
                                "%Y-%m-%d"
                            )
                            if isinstance(user_data.get("createdAt"), datetime)
                            else user_data.get("createdAt", "")
                        ),
                    }
                )

        app.logger.info(
            f"Firestore user search query: '{query}', found {len(filtered_users)} users"
        )
        return jsonify({"users": filtered_users})

    except Exception as e:
        app.logger.error(f"Firestore user search failed: {e}")
        return jsonify({"error": "User search failed"}), 500


@app.route("/api/admin/clear-rate-limits", methods=["GET", "POST"])
def clear_rate_limits():
    """管理用：レート制限をクリア"""
    try:
        global rate_limit_storage
        cleared_count = len(rate_limit_storage)
        rate_limit_storage.clear()
        app.logger.info(
            f"Rate limits cleared by admin (cleared {cleared_count} entries)"
        )
        return jsonify(
            {
                "message": "Rate limits cleared successfully",
                "status": "success",
                "cleared_entries": cleared_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
    except Exception as e:
        app.logger.error(f"Failed to clear rate limits: {e}")
        return jsonify({"error": "Failed to clear rate limits"}), 500


@app.route("/api/users/<user_id>/profile", methods=["GET"])
def get_user_profile(user_id):
    """実際のFirestoreユーザープロフィール取得 - デバッグ強化版"""
    try:
        app.logger.info(f"🔍 [DEBUG] Getting profile for user: {user_id}")
        app.logger.info(f"🔍 [DEBUG] Firestore db object status: {db is not None}")

        # Firestoreデータベース接続チェック
        if db is None:
            app.logger.warning(
                "🟡 [DEBUG] Firestore database not configured, returning mock profile"
            )
            # 開発環境向けのモックプロフィールを返す
            mock_profile = {
                "userId": user_id,
                "displayName": user_id.replace("user_", "")
                .replace("_dev", "")
                .replace("_", "@"),
                "email": user_id.replace("user_", "")
                .replace("_dev", "")
                .replace("_", "@"),
                "bio": DEFAULT_BIO_MESSAGE,
                "trackCount": 0,
                "totalDurationMinutes": 0,
                "followersCount": 0,
                "joinedDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "avatarUrl": "",
                "tracks": [],
            }
            app.logger.info(
                f"✅ [DEBUG] Mock profile generated successfully for {user_id}"
            )
            return jsonify({"profile": mock_profile, "status": "success", "mock": True})

        # Firestoreからユーザープロフィールを取得
        app.logger.info(
            f"🔍 [DEBUG] Attempting to get user profile document from Firestore"
        )
        user_profile_ref = db.collection("user_profiles").document(user_id)
        app.logger.info(f"🔍 [DEBUG] Created document reference for {user_id}")
        user_profile_doc = user_profile_ref.get()
        app.logger.info(
            f"🔍 [DEBUG] Retrieved document, exists: {user_profile_doc.exists}"
        )

        if not user_profile_doc.exists:
            app.logger.warning(
                f"🟡 [DEBUG] User profile not found in Firestore: {user_id}, creating mock profile"
            )
            # プロフィールが存在しない場合は自動で作成（404を返さない）
            mock_profile = {
                "userId": user_id,
                "displayName": f"User {user_id[:8]}",
                "email": f"user_{user_id[:8]}@example.com",
                "bio": DEFAULT_BIO_MESSAGE,
                "trackCount": 0,
                "totalDurationMinutes": 0,
                "followersCount": 0,
                "joinedDate": datetime.utcnow().strftime("%Y-%m-%d"),
                "avatarUrl": "",
                "tracks": [],
            }
            app.logger.info(f"✅ [DEBUG] Auto-created mock profile for {user_id}")
            return jsonify(
                {
                    "profile": mock_profile,
                    "status": "success",
                    "mock": True,
                    "autoCreated": True,
                }
            )

        user_data = user_profile_doc.to_dict()
        app.logger.info(
            f"🔍 [DEBUG] User data retrieved: {list(user_data.keys()) if user_data else 'None'}"
        )

        # ユーザーの実際のトラックを取得（インデックス不要のシンプルなクエリ）
        app.logger.info(f"🔍 [DEBUG] Querying tracks for user: {user_id}")
        user_tracks_query = db.collection("tracks").where("uploaderUid", "==", user_id)
        app.logger.info(f"🔍 [DEBUG] Created tracks query")
        user_tracks_docs = user_tracks_query.stream()
        app.logger.info(f"🔍 [DEBUG] Started streaming tracks documents")

        tracks = []
        total_duration_sec = 0
        track_count = 0
        all_tracks = []

        for track_doc in user_tracks_docs:
            track_data = track_doc.to_dict()
            track_id = track_doc.id

            # パブリックトラックのみを含める
            if track_data.get("visibility", "private") == "public":
                duration = track_data.get("durationSec", 0)
                total_duration_sec += duration
                track_count += 1

                # createdAtをパースして比較可能にする
                created_at = track_data.get("createdAt", datetime.utcnow())
                if not isinstance(created_at, datetime):
                    try:
                        created_at = (
                            datetime.fromisoformat(str(created_at))
                            if created_at
                            else datetime.utcnow()
                        )
                    except:
                        created_at = datetime.utcnow()

                all_tracks.append(
                    {
                        "trackId": track_id,
                        "title": track_data.get("title", "Untitled Track"),
                        "description": track_data.get("description", ""),
                        "durationSec": duration,
                        "createdAt": created_at.strftime("%Y-%m-%d"),
                        "createdAtSort": created_at,
                    }
                )

        # Python側で日付順にソート（新しい順）
        tracks = sorted(all_tracks, key=lambda x: x["createdAtSort"], reverse=True)
        # ソート用のフィールドを削除
        for track in tracks:
            del track["createdAtSort"]

        # プロフィールデータを構築
        profile = {
            "userId": user_id,
            "displayName": user_data.get("displayName", "Unknown User"),
            "email": user_data.get("email", ""),
            "bio": user_data.get("bio", DEFAULT_BIO_MESSAGE),
            "trackCount": track_count,
            "totalDurationMinutes": total_duration_sec // 60,
            "followersCount": user_data.get("followersCount", 0),
            "joinedDate": (
                user_data.get("createdAt", datetime.utcnow()).strftime("%Y-%m-%d")
                if isinstance(user_data.get("createdAt"), datetime)
                else str(user_data.get("createdAt", ""))
            ),
            "avatarUrl": user_data.get("avatarUrl", ""),
            "tracks": tracks,
        }

        app.logger.info(
            f"✅ [DEBUG] Retrieved Firestore profile for user: {user_id}, tracks: {track_count}"
        )
        app.logger.info(f"✅ [DEBUG] Profile data keys: {list(profile.keys())}")

        return jsonify({"profile": profile, "status": "success"})

    except Exception as e:
        app.logger.error(f"🚨 [DEBUG] Exception in get_user_profile for {user_id}: {e}")
        app.logger.error(f"🚨 [DEBUG] Error type: {type(e).__name__}")
        app.logger.error(f"🚨 [DEBUG] Error details: {str(e)}")
        app.logger.error(f"🚨 [DEBUG] Full traceback: ", exc_info=True)

        # HTTP 500エラーではなく、正常なJSONレスポンスでフォールバック
        app.logger.info(f"🔄 [DEBUG] Returning fallback profile for {user_id}")
        fallback_profile = {
            "userId": user_id,
            "displayName": user_id.replace("user_", "")
            .replace("_dev", "")
            .replace("_", "@"),
            "email": user_id.replace("user_", "").replace("_dev", "").replace("_", "@"),
            "bio": "プロフィール取得中にエラーが発生しました。開発環境用のプロフィールです。",
            "trackCount": 0,
            "totalDurationMinutes": 0,
            "followersCount": 0,
            "joinedDate": datetime.utcnow().strftime("%Y-%m-%d"),
            "avatarUrl": "",
            "tracks": [],
        }

        app.logger.info(f"✅ [DEBUG] Fallback profile created for {user_id}")
        return (
            jsonify(
                {
                    "profile": fallback_profile,
                    "status": "success",
                    "error_handled": True,
                    "original_error": str(e),
                }
            ),
            200,
        )  # 明示的に200ステータスを指定


# User Profile Creation/Update Endpoint
@app.route("/api/users/profile", methods=["POST"])
@verify_token
def create_or_update_user_profile():
    """ユーザープロフィール作成・更新"""
    try:
        user_uid = request.user_uid
        user_email = getattr(request, "user_email", "")

        # リクエストからプロフィール情報を取得
        data = request.get_json() or {}
        display_name = data.get(
            "displayName", user_email.split("@")[0] if user_email else "Unknown User"
        )
        bio = data.get("bio", "")
        website = data.get("website", "")
        location = data.get("location", "")

        # Firestoreがnullの場合（初期化エラー）はスキップしてダミー応答を返す
        if db is None:
            app.logger.warning("Firestore not initialized, skipping profile creation")
            return jsonify(
                {
                    "status": "success",
                    "action": "skipped",
                    "userId": user_uid,
                    "displayName": display_name,
                    "message": "Profile creation skipped (database not available)",
                }
            )

        # Firestoreのuser_profilesコレクションを確認・作成
        user_profile_ref = db.collection("user_profiles").document(user_uid)
        user_profile_doc = user_profile_ref.get()

        current_time = datetime.utcnow()

        if user_profile_doc.exists:
            # 既存プロフィールの更新
            user_profile_ref.update(
                {
                    "displayName": display_name,
                    "bio": bio,
                    "website": website,
                    "location": location,
                    "updatedAt": current_time,
                }
            )
            app.logger.info(f"Updated profile for user: {user_uid}")
            action = "updated"
        else:
            # 新規プロフィール作成
            user_profile_ref.set(
                {
                    "userId": user_uid,
                    "email": user_email,
                    "displayName": display_name,
                    "bio": bio,
                    "website": website,
                    "location": location,
                    "followersCount": 0,
                    "avatarUrl": "",
                    "createdAt": current_time,
                    "updatedAt": current_time,
                }
            )
            app.logger.info(f"Created new profile for user: {user_uid}")
            action = "created"

        return jsonify(
            {
                "status": "success",
                "action": action,
                "userId": user_uid,
                "displayName": display_name,
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to create/update user profile: {e}")
        return jsonify({"error": "Failed to create/update user profile"}), 500


# =====================================================
# PLAYLIST MANAGEMENT APIs
# =====================================================


@app.route("/api/playlists", methods=["GET"])
@verify_token
def get_user_playlists():
    """ユーザーのプレイリスト一覧取得"""
    try:
        # デバッグ用ログ追加
        app.logger.info(
            f"🔍 Getting playlists for user: {getattr(request, 'user_uid', 'NO_UID')}"
        )

        if db is None:
            app.logger.warning("⚠️ Database not configured - returning 503")
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = getattr(request, "user_uid", None)
        if not user_uid:
            app.logger.error("❌ No user_uid found in request")
            return jsonify({"error": "User authentication failed"}), 401

        # ユーザーのプレイリストを取得
        playlists_ref = db.collection("playlists").where("creatorUid", "==", user_uid)
        playlists = []

        try:
            for doc in playlists_ref.get():
                playlist_data = doc.to_dict()
                playlist_data["playlistId"] = doc.id
                playlists.append(playlist_data)
        except Exception as query_error:
            app.logger.warning(f"⚠️ No playlists found or query error: {query_error}")
            # プレイリストが存在しない場合は空のリストを返す
            playlists = []

        # 作成日時でソート（新しい順）
        playlists.sort(key=lambda x: x.get("createdAt", ""), reverse=True)

        app.logger.info(f"✅ Found {len(playlists)} playlists for user {user_uid}")

        return jsonify({"playlists": playlists, "count": len(playlists)})

    except Exception as e:
        app.logger.error(f"❌ Failed to get user playlists: {e}", exc_info=True)
        return (
            jsonify({"error": "Failed to retrieve playlists", "details": str(e)}),
            500,
        )


@app.route("/api/playlists", methods=["POST"])
@verify_token
def create_playlist():
    """プレイリスト作成"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid
        data = request.get_json(force=True)

        if not data:
            return jsonify({"error": "Request body is required"}), 400

        # プレイリスト名（必須）
        name = data.get("name")
        if not name or not name.strip():
            return jsonify({"error": "Playlist name is required"}), 400
        name = name.strip()

        if len(name) > 100:
            return (
                jsonify({"error": "Playlist name must be 100 characters or less"}),
                400,
            )

        # 説明（オプション）
        description = data.get("description")
        if description:
            description = description.strip()
            if len(description) > 500:
                return (
                    jsonify({"error": "Description must be 500 characters or less"}),
                    400,
                )

        # 絵文字（オプション）
        emoji = data.get("emoji", "🎵")

        # 公開設定（オプション、フロントエンドからはisPrivateで送信される）
        is_private = data.get("isPrivate", True)  # デフォルトはプライベート
        is_public = not is_private  # isPrivateの逆がisPublic

        # プレイリストデータ準備
        playlist_data = {
            "name": name,
            "description": description or None,
            "emoji": emoji,
            "creatorUid": user_uid,
            "tracks": [],  # 初期は空のトラックリスト
            "trackCount": 0,
            "totalDuration": 0,
            "isPublic": is_public,
            "isPrivate": is_private,  # 新しく追加
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
        }

        # Firestoreに保存
        doc_ref = db.collection("playlists").add(playlist_data)
        playlist_id = doc_ref[1].id  # doc_ref is a tuple (timestamp, DocumentReference)

        app.logger.info(f"✅ Playlist created: {playlist_id} by user {user_uid}")

        return (
            jsonify(
                {
                    "message": "Playlist created successfully",
                    "playlistId": playlist_id,
                    "name": name,
                }
            ),
            201,
        )

    except Exception as e:
        app.logger.error(f"Failed to create playlist: {e}")
        return jsonify({"error": "Failed to create playlist"}), 500


@app.route("/api/playlists/<playlist_id>/podcast-episodes", methods=["POST"])
@verify_token
def add_podcast_episode_to_playlist(playlist_id):
    """プレイリストにポッドキャストエピソードを追加"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid
        data = request.get_json(force=True)

        if not data or not data.get("episodeId"):
            return jsonify({"error": "Episode ID is required"}), 400

        episode_id = data.get("episodeId")
        title = data.get("title", "Untitled Episode")
        description = data.get("description", "")

        # プレイリスト存在確認と権限チェック
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only modify your own playlists."}
                ),
                403,
            )

        # 既にプレイリストに存在するかチェック
        current_tracks = playlist_data.get("tracks", [])
        podcast_episodes = playlist_data.get("podcastEpisodes", [])

        # Check if episode already exists
        if episode_id in current_tracks or any(
            ep.get("episodeId") == episode_id for ep in podcast_episodes
        ):
            return jsonify({"error": "Episode is already in the playlist"}), 409

        # ポッドキャストエピソードを追加
        episode_data = {
            "episodeId": episode_id,
            "title": title,
            "description": description,
            "type": "podcast",
            "addedAt": data.get("addedAt", datetime.utcnow().isoformat()),
            "audioUrl": data.get("audioUrl"),  # 音声URL追加
            "audio_url": data.get("audioUrl"),  # 後方互換性のため
            "uploaderName": data.get("uploaderName", "Podcast"),
            "duration": data.get("duration", "Unknown"),
        }

        podcast_episodes.append(episode_data)

        # プレイリスト更新
        update_data = {
            "podcastEpisodes": podcast_episodes,
            "trackCount": len(current_tracks) + len(podcast_episodes),
            "updatedAt": datetime.utcnow(),
        }

        db.collection("playlists").document(playlist_id).update(update_data)

        app.logger.info(
            f"✅ Podcast episode {episode_id} added to playlist {playlist_id} by user {user_uid}"
        )

        return (
            jsonify(
                {
                    "message": "Podcast episode added to playlist successfully",
                    "episodeId": episode_id,
                    "playlistId": playlist_id,
                }
            ),
            201,
        )

    except Exception as e:
        app.logger.error(
            f"❌ Failed to add podcast episode to playlist: {e}", exc_info=True
        )
        return (
            jsonify({"error": "Failed to add episode to playlist", "details": str(e)}),
            500,
        )


@app.route("/api/playlists/<playlist_id>/clear-podcast-episodes", methods=["POST"])
@verify_token
def clear_podcast_episodes_from_playlist(playlist_id):
    """プレイリストから全てのポッドキャストエピソードを削除"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid

        # プレイリスト存在確認と権限チェック
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only modify your own playlists."}
                ),
                403,
            )

        # 現在のポッドキャストエピソード数を取得
        podcast_episodes = playlist_data.get("podcastEpisodes", [])
        removed_count = len(podcast_episodes)

        # ポッドキャストエピソードを全て削除
        current_tracks = playlist_data.get("tracks", [])
        update_data = {
            "podcastEpisodes": [],  # 空配列にする
            "trackCount": len(current_tracks),  # 通常のトラックのみの数に更新
            "updatedAt": datetime.utcnow(),
        }

        db.collection("playlists").document(playlist_id).update(update_data)

        app.logger.info(
            f"✅ Cleared {removed_count} podcast episodes from playlist {playlist_id} by user {user_uid}"
        )

        return (
            jsonify(
                {
                    "message": f"Successfully removed {removed_count} podcast episodes from playlist",
                    "removedCount": removed_count,
                    "playlistId": playlist_id,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Failed to clear podcast episodes from playlist: {e}")
        return jsonify({"error": "Failed to clear podcast episodes"}), 500


@app.route(
    "/api/playlists/<playlist_id>/podcast-episodes/<episode_id>", methods=["DELETE"]
)
@verify_token
def remove_podcast_episode_from_playlist(playlist_id, episode_id):
    """プレイリストから個別のポッドキャストエピソードを削除"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid

        # プレイリスト存在確認と権限チェック（通常プレイリストとポッドキャストプレイリストの両方をチェック）
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        playlist_collection = "playlists"

        if not playlist_doc.exists:
            # 通常のプレイリストで見つからない場合、ポッドキャストプレイリストをチェック
            playlist_doc = (
                db.collection("podcast_playlists").document(playlist_id).get()
            )
            playlist_collection = "podcast_playlists"

            if not playlist_doc.exists:
                return (
                    jsonify({"error": "Playlist not found in either collection"}),
                    404,
                )

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only modify your own playlists."}
                ),
                403,
            )

        # ポッドキャストエピソードから削除を試行
        current_podcast_episodes = playlist_data.get("podcastEpisodes", [])

        episode_found = False
        episode_title = "Unknown Episode"

        # episode_idで一致するエピソードを探して削除
        for i, episode in enumerate(current_podcast_episodes):
            if (
                episode.get("trackId") == episode_id
                or episode.get("episodeId") == episode_id
            ):
                episode_title = episode.get("title", "Unknown Episode")
                current_podcast_episodes.pop(i)
                episode_found = True
                break

        if not episode_found:
            return jsonify({"error": "Episode not found in this playlist"}), 404

        # プレイリスト更新
        current_tracks = playlist_data.get("tracks", [])
        update_data = {
            "tracks": current_tracks,
            "podcastEpisodes": current_podcast_episodes,
            "trackCount": len(current_tracks) + len(current_podcast_episodes),
            "updatedAt": datetime.utcnow(),
        }

        db.collection(playlist_collection).document(playlist_id).update(update_data)

        app.logger.info(
            f"✅ Podcast episode {episode_id} removed from playlist {playlist_id} by user {user_uid}"
        )

        return jsonify(
            {
                "message": "Episode removed from playlist successfully",
                "playlistId": playlist_id,
                "episodeId": episode_id,
                "episodeTitle": episode_title,
                "trackCount": update_data["trackCount"],
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to remove podcast episode from playlist: {e}")
        return jsonify({"error": "Failed to remove episode from playlist"}), 500


@app.route("/api/maintenance/clear-invalid-podcasts", methods=["POST"])
def maintenance_clear_invalid_podcasts():
    """メンテナンス用: audioURLが無効なポッドキャストエピソードを全てのプレイリストから削除"""
    try:
        if db is None:
            return jsonify({"error": "Database not configured"}), 503

        # セキュリティ: メンテナンスキーをチェック
        maintenance_key = (
            request.json.get("maintenance_key") if request.is_json else None
        )
        if maintenance_key != "cleanup_invalid_podcasts_2024":
            return jsonify({"error": "Invalid maintenance key"}), 403

        total_removed = 0
        updated_playlists = []

        # 全てのプレイリストを取得
        playlists = db.collection("playlists").get()

        for playlist_doc in playlists:
            playlist_id = playlist_doc.id
            playlist_data = playlist_doc.to_dict()
            podcast_episodes = playlist_data.get("podcastEpisodes", [])

            if not podcast_episodes:
                continue

            # audioURLが無効なエピソードをフィルター
            valid_episodes = []
            removed_count = 0

            for episode in podcast_episodes:
                audio_url = episode.get("audioUrl") or episode.get("audio_url")
                if audio_url and audio_url.strip() and audio_url != "undefined":
                    valid_episodes.append(episode)
                else:
                    removed_count += 1

            # 無効なエピソードがあった場合のみ更新
            if removed_count > 0:
                current_tracks = playlist_data.get("tracks", [])
                update_data = {
                    "podcastEpisodes": valid_episodes,
                    "trackCount": len(current_tracks) + len(valid_episodes),
                    "updatedAt": datetime.utcnow(),
                }

                db.collection("playlists").document(playlist_id).update(update_data)

                total_removed += removed_count
                updated_playlists.append(
                    {
                        "playlistId": playlist_id,
                        "removedCount": removed_count,
                        "remainingCount": len(valid_episodes),
                    }
                )

                app.logger.info(
                    f"🧹 Maintenance: Removed {removed_count} invalid podcast episodes from playlist {playlist_id}"
                )

        return (
            jsonify(
                {
                    "message": f"Maintenance completed: Removed {total_removed} invalid podcast episodes",
                    "totalRemoved": total_removed,
                    "updatedPlaylists": updated_playlists,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Maintenance operation failed: {e}")
        return (
            jsonify({"error": "Maintenance operation failed", "details": str(e)}),
            500,
        )


@app.route("/api/playlists/<playlist_id>/debug", methods=["GET"])
def debug_playlist_contents(playlist_id):
    """プレイリストの内容をデバッグ用に表示（認証不要）"""
    try:
        if db is None:
            return jsonify({"error": "Database not configured"}), 503

        playlist_doc = db.collection("playlists").document(playlist_id).get()
        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()

        return (
            jsonify(
                {
                    "playlistId": playlist_id,
                    "name": playlist_data.get("name", "Unknown"),
                    "tracks": playlist_data.get("tracks", []),
                    "podcastEpisodes": playlist_data.get("podcastEpisodes", []),
                    "trackCount": playlist_data.get("trackCount", 0),
                    "creatorUid": playlist_data.get("creatorUid"),
                    "updatedAt": playlist_data.get("updatedAt"),
                    "message": f"Found {len(playlist_data.get('tracks', []))} tracks and {len(playlist_data.get('podcastEpisodes', []))} podcast episodes",
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"❌ Failed to debug playlist: {e}", exc_info=True)
        return (
            jsonify({"error": "Failed to get playlist debug info", "details": str(e)}),
            500,
        )


@app.route("/api/tracks/debug", methods=["GET"])
def debug_tracks():
    """トラック情報をデバッグ用に表示（認証不要）"""
    try:
        if db is None:
            return jsonify({"error": "Database not configured"}), 503

        # Check multiple collections that might contain track data
        debug_info = {"collections_checked": [], "tracks_found": 0, "tracks": []}

        # Collection names to check
        collection_names = ["transcripts", "tracks", "episodes", "podcasts", "uploads"]

        for collection_name in collection_names:
            try:
                docs = db.collection(collection_name).stream()
                collection_data = []

                for doc in docs:
                    track_data = doc.to_dict()
                    collection_data.append(
                        {
                            "id": doc.id,
                            "title": track_data.get("title", "Unknown"),
                            "type": track_data.get("type", "unknown"),
                            "isPodcast": track_data.get("isPodcast", False),
                            "audioUrl": track_data.get("audioUrl"),
                            "audio_url": track_data.get("audio_url"),
                            "file_path": track_data.get("file_path"),
                            "uploaderName": track_data.get(
                                "uploader_name",
                                track_data.get("uploaderName", "Unknown"),
                            ),
                            "createdAt": track_data.get("created_at"),
                            "raw_keys": list(track_data.keys()),
                        }
                    )

                debug_info["collections_checked"].append(
                    {
                        "name": collection_name,
                        "count": len(collection_data),
                        "data": collection_data[:5],  # Show only first 5 for brevity
                    }
                )

                if len(collection_data) > 0:
                    debug_info["tracks_found"] += len(collection_data)
                    debug_info["tracks"].extend(collection_data)

            except Exception as e:
                debug_info["collections_checked"].append(
                    {"name": collection_name, "error": str(e)}
                )

        return jsonify(debug_info), 200

    except Exception as e:
        app.logger.error(f"❌ Failed to debug tracks: {e}", exc_info=True)
        return (
            jsonify({"error": "Failed to get tracks debug info", "details": str(e)}),
            500,
        )


@app.route("/api/tracks/by-ids", methods=["POST"])
@verify_token
def get_tracks_by_ids():
    """特定のトラックIDリストに基づいてトラック情報を取得（プレイリスト表示用）"""
    try:
        if db is None:
            return jsonify({"error": "Database not configured"}), 503

        # リクエストボディからトラックIDリストを取得
        data = request.get_json()
        if not data or "trackIds" not in data:
            return jsonify({"error": "trackIds array required in request body"}), 400

        track_ids = data["trackIds"]
        if not isinstance(track_ids, list):
            return jsonify({"error": "trackIds must be an array"}), 400

        app.logger.info(f"🔍 Fetching tracks by IDs: {track_ids}")

        tracks = []

        # 各トラックIDについて個別に取得
        for track_id in track_ids:
            try:
                doc = db.collection("tracks").document(track_id).get()
                if doc.exists:
                    track_data = doc.to_dict()
                    track_data["trackId"] = doc.id

                    # createdAtをISO文字列に変換
                    if "createdAt" in track_data and track_data["createdAt"]:
                        try:
                            track_data["createdAt"] = track_data[
                                "createdAt"
                            ].isoformat()
                        except:
                            track_data["createdAt"] = str(track_data["createdAt"])
                    if "updatedAt" in track_data and track_data["updatedAt"]:
                        try:
                            track_data["updatedAt"] = track_data[
                                "updatedAt"
                            ].isoformat()
                        except:
                            track_data["updatedAt"] = str(track_data["updatedAt"])

                    tracks.append(track_data)
                    app.logger.info(
                        f"✅ Found track: {track_id} - {track_data.get('title', 'Unknown')}"
                    )
                else:
                    app.logger.warning(f"❌ Track not found: {track_id}")

            except Exception as e:
                app.logger.error(f"Error fetching track {track_id}: {e}")
                continue

        app.logger.info(
            f"📊 Returning {len(tracks)} tracks from {len(track_ids)} requested IDs"
        )
        return jsonify({"tracks": tracks}), 200

    except Exception as e:
        app.logger.error(f"❌ Failed to get tracks by IDs: {e}", exc_info=True)
        return jsonify({"error": "Failed to get tracks by IDs", "details": str(e)}), 500


@app.route("/api/playlists/<playlist_id>", methods=["DELETE"])
@verify_token
def delete_playlist(playlist_id):
    """プレイリスト削除"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid

        # プレイリスト存在確認と権限チェック
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only delete your own playlists."}
                ),
                403,
            )

        # プレイリスト削除
        db.collection("playlists").document(playlist_id).delete()

        app.logger.info(f"✅ Playlist deleted: {playlist_id} by user {user_uid}")

        return jsonify(
            {"message": "Playlist deleted successfully", "playlistId": playlist_id}
        )

    except Exception as e:
        app.logger.error(f"Failed to delete playlist {playlist_id}: {e}")
        return jsonify({"error": "Failed to delete playlist"}), 500


@app.route("/api/playlists/<playlist_id>/tracks", methods=["POST"])
@verify_token
def add_track_to_playlist(playlist_id):
    """プレイリストにトラックを追加"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid
        data = request.get_json(force=True)

        if not data or not data.get("trackId"):
            return jsonify({"error": "Track ID is required"}), 400

        track_id = data.get("trackId")

        # プレイリスト存在確認と権限チェック
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only modify your own playlists."}
                ),
                403,
            )

        # トラック存在確認
        track_doc = db.collection("tracks").document(track_id).get()
        if not track_doc.exists:
            return jsonify({"error": "Track not found"}), 404

        # 既にプレイリストに存在するかチェック
        current_tracks = playlist_data.get("tracks", [])
        if track_id in current_tracks:
            return jsonify({"error": "Track is already in the playlist"}), 400

        # トラックを追加
        current_tracks.append(track_id)
        track_data = track_doc.to_dict()

        # プレイリスト更新
        update_data = {
            "tracks": current_tracks,
            "trackCount": len(current_tracks),
            "totalDuration": playlist_data.get("totalDuration", 0)
            + track_data.get("duration", 0),
            "updatedAt": datetime.utcnow(),
        }

        db.collection("playlists").document(playlist_id).update(update_data)

        app.logger.info(
            f"✅ Track {track_id} added to playlist {playlist_id} by user {user_uid}"
        )

        return jsonify(
            {
                "message": "Track added to playlist successfully",
                "playlistId": playlist_id,
                "trackId": track_id,
                "trackCount": len(current_tracks),
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to add track to playlist: {e}")
        return jsonify({"error": "Failed to add track to playlist"}), 500


@app.route("/api/playlists/<playlist_id>/tracks/<track_id>", methods=["DELETE"])
@verify_token
def remove_track_from_playlist(playlist_id, track_id):
    """プレイリストからトラックを削除"""
    try:
        if db is None:
            return (
                jsonify(
                    {"error": "Playlist service unavailable (database not configured)"}
                ),
                503,
            )

        user_uid = request.user_uid

        # プレイリスト存在確認と権限チェック（通常プレイリストとポッドキャストプレイリストの両方をチェック）
        playlist_doc = db.collection("playlists").document(playlist_id).get()
        playlist_collection = "playlists"

        if not playlist_doc.exists:
            # 通常のプレイリストで見つからない場合、ポッドキャストプレイリストをチェック
            playlist_doc = (
                db.collection("podcast_playlists").document(playlist_id).get()
            )
            playlist_collection = "podcast_playlists"

            if not playlist_doc.exists:
                return (
                    jsonify({"error": "Playlist not found in either collection"}),
                    404,
                )

        playlist_data = playlist_doc.to_dict()
        if playlist_data.get("creatorUid") != user_uid:
            return (
                jsonify(
                    {"error": "Access denied. You can only modify your own playlists."}
                ),
                403,
            )

        # 通常の音楽トラックとポッドキャストエピソードの両方をチェック
        current_tracks = playlist_data.get("tracks", [])
        current_podcast_episodes = playlist_data.get("podcastEpisodes", [])

        track_found = False
        track_title = "Unknown Track"
        track_duration = 0

        # 音楽トラックから削除を試行
        if track_id in current_tracks:
            current_tracks.remove(track_id)
            track_found = True

            # トラック情報を取得（削除前）
            try:
                track_doc = db.collection("tracks").document(track_id).get()
                if track_doc.exists:
                    track_data = track_doc.to_dict()
                    track_title = track_data.get("title", "Unknown Track")
                    track_duration = track_data.get("duration", 0)
            except Exception as e:
                app.logger.warning(f"Failed to get track data for {track_id}: {e}")

        # ポッドキャストエピソードから削除を試行
        elif track_id in current_podcast_episodes:
            current_podcast_episodes.remove(track_id)
            track_found = True

            # ポッドキャストエピソード情報を取得（削除前）
            try:
                episode_doc = db.collection("podcast_episodes").document(track_id).get()
                if episode_doc.exists:
                    episode_data = episode_doc.to_dict()
                    track_title = episode_data.get("title", "Unknown Episode")
                    track_duration = episode_data.get("duration", 0)
            except Exception as e:
                app.logger.warning(f"Failed to get episode data for {track_id}: {e}")

        if not track_found:
            return jsonify({"error": "Track not found in this playlist"}), 404

        # 総再生時間を更新（duration が負になるのを防ぐ）
        current_total_duration = playlist_data.get("totalDuration", 0)
        new_total_duration = max(0, current_total_duration - track_duration)

        # プレイリスト更新
        update_data = {
            "tracks": current_tracks,
            "podcastEpisodes": current_podcast_episodes,
            "trackCount": len(current_tracks) + len(current_podcast_episodes),
            "totalDuration": new_total_duration,
            "updatedAt": datetime.utcnow(),
        }

        db.collection(playlist_collection).document(playlist_id).update(update_data)

        app.logger.info(
            f"✅ Track {track_id} removed from playlist {playlist_id} by user {user_uid}"
        )

        return jsonify(
            {
                "message": "Track removed from playlist successfully",
                "playlistId": playlist_id,
                "trackId": track_id,
                "trackTitle": track_title,
                "trackCount": update_data["trackCount"],
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to remove track from playlist: {e}")
        return jsonify({"error": "Failed to remove track from playlist"}), 500


# =================================
# ポッドキャスト検索機能
# =================================

# 日本の有名なポッドキャストフィード（大幅拡充版）
JAPANESE_TECH_PODCASTS = {
    # テクノロジー・AI系
    "rebuild": {
        "name": "Rebuild",
        "rss_url": "https://feeds.rebuild.fm/rebuildfm",
        "description": "宮川達彦による技術系ポッドキャスト、AI話題も多数",
        "category": "tech",
        "language": "ja",
    },
    "researchat": {
        "name": "Researchat.fm",
        "rss_url": "https://anchor.fm/s/2bf53a0/podcast/rss",
        "description": "研究者による最先端研究について語るポッドキャスト、AI・機械学習が頻出",
        "category": "research",
        "language": "ja",
    },
    "ajito": {
        "name": "ajito.fm",
        "rss_url": "https://anchor.fm/s/10100e64/podcast/rss",
        "description": "AI/MLエンジニアが運営する機械学習専門ポッドキャスト",
        "category": "ai_ml",
        "language": "ja",
    },
    "fukabori": {
        "name": "fukabori.fm",
        "rss_url": "https://fukabori.fm/feed.xml",
        "description": "技術トピックを深掘りするポッドキャスト、AI関連回も多数",
        "category": "tech",
        "language": "ja",
    },
    "turing_complete": {
        "name": "Turing Complete FM",
        "rss_url": "https://turingcomplete.fm/feed.xml",
        "description": "コンピュータサイエンス系ポッドキャスト",
        "category": "cs",
        "language": "ja",
    },
    "mozaic_fm": {
        "name": "mozaic.fm",
        "rss_url": "https://feeds.feedburner.com/mozaic-fm",
        "description": "jxckによるウェブ技術系ポッドキャスト",
        "category": "tech",
        "language": "ja",
    },
    "soussune": {
        "name": "soussune",
        "rss_url": "https://feeds.soundcloud.com/users/soundcloud:users:302817555/sounds.rss",
        "description": "プログラマー向けポッドキャスト",
        "category": "tech",
        "language": "ja",
    },
    "drikin": {
        "name": "Drikin",
        "rss_url": "https://drikin.podbean.com/feed/",
        "description": "Apple製品やテクノロジー関連トピック",
        "category": "tech",
        "language": "ja",
    },
    # ビジネス・起業系
    "voicy_business": {
        "name": "イケハヤラジオ",
        "rss_url": "https://voicy.jp/feed/ikehaya",
        "description": "ビジネス・投資・仮想通貨",
        "category": "business",
        "language": "ja",
    },
    "nikkei_podcast": {
        "name": "日経ビジネス",
        "rss_url": "https://www.nikkei.com/article/DGXMZO00000000000000000000000000/rss/",
        "description": "日本経済・ビジネス情報",
        "category": "business",
        "language": "ja",
    },
    "startup_fm": {
        "name": "スタートアップFM",
        "rss_url": "https://anchor.fm/s/startup-fm/podcast/rss",
        "description": "スタートアップ・起業家向けコンテンツ",
        "category": "business",
        "language": "ja",
    },
    # エンターテインメント・文化系
    "coten_radio": {
        "name": "COTEN RADIO",
        "rss_url": "https://cotenradio.fm/feed",
        "description": "歴史を深く楽しく学ぶポッドキャスト",
        "category": "culture",
        "language": "ja",
    },
    "tbs_radio": {
        "name": "TBSラジオ クラウド",
        "rss_url": "https://www.tbsradio.jp/podcasting/rss/all.xml",
        "description": "TBSラジオの人気番組アーカイブ",
        "category": "entertainment",
        "language": "ja",
    },
    "nihon_no_hanashi": {
        "name": "日本の話芸",
        "rss_url": "https://www.nhk.or.jp/radio/podcast/rss/hanageijp.xml",
        "description": "NHKの話芸番組",
        "category": "culture",
        "language": "ja",
    },
    # ニュース・報道系
    "nhk_news": {
        "name": "NHKラジオニュース",
        "rss_url": "https://www.nhk.or.jp/r1/podcast/rss/news.xml",
        "description": "NHKの最新ニュース",
        "category": "news",
        "language": "ja",
    },
    "asahi_podcast": {
        "name": "朝日新聞ポッドキャスト",
        "rss_url": "https://www.asahi.com/podcast/rss/news.xml",
        "description": "朝日新聞のニュース解説",
        "category": "news",
        "language": "ja",
    },
    # 教育・学習系
    "bbc_learning": {
        "name": "BBC Learning English",
        "rss_url": "https://podcasts.files.bbci.co.uk/p02pc9tn.rss",
        "description": "英語学習向けポッドキャスト",
        "category": "education",
        "language": "en",
    },
    "ted_talks": {
        "name": "TED Talks Daily",
        "rss_url": "https://feeds.feedburner.com/tedtalks_audio",
        "description": "TED講演の音声版",
        "category": "education",
        "language": "en",
    },
    # サイエンス・研究系
    "science_podcast": {
        "name": "サイエンストーク",
        "rss_url": "https://anchor.fm/s/science-talk/podcast/rss",
        "description": "科学研究・技術トレンドを語る",
        "category": "science",
        "language": "ja",
    },
    "medical_note": {
        "name": "Medical Note",
        "rss_url": "https://anchor.fm/s/medical-note/podcast/rss",
        "description": "医療・健康に関する情報",
        "category": "health",
        "language": "ja",
    },
    # 国際・グローバル系
    "joe_rogan": {
        "name": "The Joe Rogan Experience",
        "rss_url": "https://feeds.spotify.com/joe-rogan",
        "description": "人気の長時間対談ポッドキャスト",
        "category": "entertainment",
        "language": "en",
    },
    "this_american_life": {
        "name": "This American Life",
        "rss_url": "https://feeds.thisamericanlife.org/talpodcast",
        "description": "アメリカの人気ストーリーテリングポッドキャスト",
        "category": "culture",
        "language": "en",
    },
    "serial": {
        "name": "Serial",
        "rss_url": "https://feeds.serialpodcast.org/serial",
        "description": "調査報道ポッドキャストの金字塔",
        "category": "news",
        "language": "en",
    },
    # 追加の日本語ポッドキャスト
    "horiemon_channel": {
        "name": "ホリエモンチャンネル",
        "rss_url": "https://anchor.fm/s/horiemon/podcast/rss",
        "description": "堀江貴文のビジネス・テクノロジー論",
        "category": "business",
        "language": "ja",
    },
    "newspicks": {
        "name": "NewsPicks",
        "rss_url": "https://anchor.fm/s/newspicks/podcast/rss",
        "description": "経済ニュースの深掘り解説",
        "category": "business",
        "language": "ja",
    },
}


def search_episodes_by_keywords(keywords, max_results=200):
    """キーワードでエピソードを検索"""
    results = []
    keywords_lower = [k.lower() for k in keywords]

    for podcast_id, podcast_info in JAPANESE_TECH_PODCASTS.items():
        try:
            app.logger.info(f"🔍 Fetching RSS feed for {podcast_info['name']}")

            # RSSフィードを取得
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; AIIV-Podcast-Search/1.0)"
            }
            response = requests.get(
                podcast_info["rss_url"], headers=headers, timeout=10
            )
            response.raise_for_status()

            # フィードを解析
            feed = feedparser.parse(response.content)

            if not feed.entries:
                app.logger.warning(f"No entries found for {podcast_info['name']}")
                continue

            app.logger.info(
                f"📊 Found {len(feed.entries)} episodes in {podcast_info['name']}"
            )

            # エピソードをキーワードでフィルタ
            for entry in feed.entries[:50]:  # 最新50件をチェック
                title = entry.get("title", "").lower()
                description = entry.get("description", "").lower()
                summary = entry.get("summary", "").lower()

                # キーワードマッチング
                content_text = f"{title} {description} {summary}"
                keyword_matches = []

                # ユーザー指定のキーワードのみマッチング（自動追加なし）
                for keyword in keywords_lower:
                    if keyword in content_text:
                        keyword_matches.append(keyword)

                if (
                    keyword_matches or not keywords
                ):  # キーワードが一致するか、キーワード指定なしの場合
                    # エピソード情報を構築
                    episode = {
                        "id": f"{podcast_id}_{hash(entry.get('link', ''))}",
                        "title": entry.get("title", "Untitled"),
                        "description": entry.get("description", "")[:500]
                        + ("..." if len(entry.get("description", "")) > 500 else ""),
                        "summary": entry.get("summary", "")[:300]
                        + ("..." if len(entry.get("summary", "")) > 300 else ""),
                        "published": entry.get("published", ""),
                        "published_parsed": entry.get("published_parsed", None),
                        "duration": entry.get("itunes_duration", "Unknown"),
                        "audio_url": None,
                        "link": entry.get("link", ""),
                        "podcast_name": podcast_info["name"],
                        "podcast_id": podcast_id,
                        "category": podcast_info["category"],
                        "matched_keywords": keyword_matches,
                        "language": "ja",
                    }

                    # 音声ファイルURLを取得
                    if hasattr(entry, "enclosures") and entry.enclosures:
                        for enclosure in entry.enclosures:
                            if enclosure.type and "audio" in enclosure.type:
                                episode["audio_url"] = enclosure.href
                                break

                    # Linkからも音声URLを探す
                    if not episode["audio_url"] and hasattr(entry, "links"):
                        for link in entry.links:
                            if link.type and "audio" in link.type:
                                episode["audio_url"] = link.href
                                break

                    results.append(episode)

                    if len(results) >= max_results:
                        break

        except Exception as e:
            app.logger.error(f"❌ Error fetching {podcast_info['name']}: {e}")
            continue

    # 日付でソート（新しい順）
    results.sort(
        key=lambda x: x.get("published_parsed") or (0, 0, 0, 0, 0, 0), reverse=True
    )

    return results[:max_results]


@app.route("/api/podcasts/search", methods=["GET"])
def search_podcasts():
    """ポッドキャスト検索API"""
    try:
        # クエリパラメータを取得（queryとqの両方に対応）
        query = request.args.get("query", request.args.get("q", "")).strip()
        category = request.args.get("category", "all")
        limit = min(int(request.args.get("limit", 100)), 500)

        app.logger.info(
            f"🔍 Podcast search: query='{query}', category='{category}', limit={limit}"
        )

        # キーワードを分割
        keywords = []
        if query:
            keywords = [w.strip() for w in query.split() if w.strip()]

        # エピソードを検索
        episodes = search_episodes_by_keywords(keywords, limit)

        # カテゴリでフィルタ
        if category != "all":
            episodes = [ep for ep in episodes if ep["category"] == category]

        app.logger.info(f"📊 Found {len(episodes)} matching episodes")

        # 結果を返す
        return jsonify(
            {
                "episodes": episodes,
                "total_count": len(episodes),
                "query": query,
                "category": category,
                "available_podcasts": list(JAPANESE_TECH_PODCASTS.keys()),
            }
        )

    except Exception as e:
        app.logger.error(f"❌ Podcast search error: {e}")
        return jsonify({"error": "Search failed", "details": str(e)}), 500


@app.route("/api/podcasts/list", methods=["GET"])
def list_podcasts():
    """利用可能なポッドキャスト一覧"""
    try:
        podcasts = []
        for podcast_id, info in JAPANESE_TECH_PODCASTS.items():
            podcasts.append(
                {
                    "id": podcast_id,
                    "name": info["name"],
                    "description": info["description"],
                    "category": info["category"],
                    "language": info["language"],
                }
            )

        return jsonify({"podcasts": podcasts, "total_count": len(podcasts)})

    except Exception as e:
        app.logger.error(f"❌ List podcasts error: {e}")
        return jsonify({"error": "Failed to list podcasts"}), 500


@app.route("/api/podcasts/subscribe", methods=["POST"])
@auth_required
def subscribe_to_podcast():
    """RSS URLを手動で追加してポッドキャストを購読"""
    try:
        data = request.get_json()
        rss_url = data.get("rss_url")

        if not rss_url:
            return jsonify({"error": "RSS URLが必要です"}), 400

        # RSS フィードをパース
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            return jsonify({"error": "無効なRSS URLです"}), 400

        # ポッドキャスト情報を抽出
        podcast_info = {
            "title": feed.feed.get("title", "Unknown Podcast"),
            "description": feed.feed.get("description", ""),
            "image": feed.feed.get("image", {}).get("href", ""),
            "rss_url": rss_url,
            "website": feed.feed.get("link", ""),
            "author": feed.feed.get("author", ""),
            "language": feed.feed.get("language", "ja"),
            "category": feed.feed.get("category", "General"),
        }

        # Firestore に保存
        user_uid = get_user_from_token()
        subscription_data = {
            "user_uid": user_uid,
            "podcast_info": podcast_info,
            "subscribed_at": datetime.utcnow(),
            "enabled": True,
            "last_fetched": None,
            "episode_count": len(feed.entries),
        }

        # 重複チェック
        subscriptions_ref = db.collection("podcast_subscriptions")
        existing = (
            subscriptions_ref.where("user_uid", "==", user_uid)
            .where("podcast_info.rss_url", "==", rss_url)
            .limit(1)
            .get()
        )

        if existing:
            return jsonify({"error": "このポッドキャストは既に購読済みです"}), 409

        # 新規購読を追加
        doc_ref = subscriptions_ref.add(subscription_data)

        return jsonify(
            {
                "message": "ポッドキャストの購読が完了しました",
                "subscription_id": doc_ref[1].id,
                "podcast_info": podcast_info,
            }
        )

    except Exception as e:
        print(f"Purchase subscription error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/podcasts/subscriptions", methods=["GET"])
@auth_required
def get_user_subscriptions():
    """ユーザーの購読リストを取得"""
    try:
        user_uid = get_user_from_token()

        subscriptions_ref = db.collection("podcast_subscriptions")
        subscriptions = (
            subscriptions_ref.where("user_uid", "==", user_uid)
            .where("enabled", "==", True)
            .order_by("subscribed_at", direction=firestore.Query.DESCENDING)
            .get()
        )

        result = []
        for doc in subscriptions:
            data = doc.to_dict()
            subscription_info = {
                "subscription_id": doc.id,
                "podcast_info": data["podcast_info"],
                "subscribed_at": (
                    data["subscribed_at"].isoformat()
                    if data.get("subscribed_at")
                    else None
                ),
                "last_fetched": (
                    data["last_fetched"].isoformat()
                    if data.get("last_fetched")
                    else None
                ),
                "episode_count": data.get("episode_count", 0),
            }
            result.append(subscription_info)

        return jsonify({"subscriptions": result})

    except Exception as e:
        print(f"Get subscriptions error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/podcasts/subscriptions/<subscription_id>", methods=["DELETE"])
@auth_required
def unsubscribe_podcast(subscription_id):
    """ポッドキャストの購読を解除"""
    try:
        user_uid = get_user_from_token()

        # 購読の存在確認
        doc_ref = db.collection("podcast_subscriptions").document(subscription_id)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "購読が見つかりません"}), 404

        subscription_data = doc.to_dict()
        if subscription_data["user_uid"] != user_uid:
            return jsonify({"error": "権限がありません"}), 403

        # 購読を無効化（完全削除ではなく）
        doc_ref.update({"enabled": False, "unsubscribed_at": datetime.utcnow()})

        return jsonify({"message": "購読を解除しました"})

    except Exception as e:
        print(f"Unsubscribe error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/podcasts/episodes/<subscription_id>", methods=["GET"])
@auth_required
def get_subscription_episodes(subscription_id):
    """特定の購読のエピソード一覧を取得"""
    try:
        user_uid = get_user_from_token()

        # 購読の存在確認
        doc_ref = db.collection("podcast_subscriptions").document(subscription_id)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "購読が見つかりません"}), 404

        subscription_data = doc.to_dict()
        if subscription_data["user_uid"] != user_uid:
            return jsonify({"error": "権限がありません"}), 403

        # RSS フィードから最新エピソードを取得
        rss_url = subscription_data["podcast_info"]["rss_url"]
        feed = feedparser.parse(rss_url)

        episodes = []
        for entry in feed.entries[:20]:  # 最新20エピソード
            # 音声URLを探す
            audio_url = None
            for link in entry.get("links", []):
                if link.get("type", "").startswith("audio/"):
                    audio_url = link.get("href")
                    break

            if not audio_url and hasattr(entry, "enclosures"):
                for enclosure in entry.enclosures:
                    if enclosure.type.startswith("audio/"):
                        audio_url = enclosure.href
                        break

            episode_info = {
                "id": f"sub_{subscription_id}_{entry.get('id', entry.get('link', ''))}",
                "title": entry.get("title", "No Title"),
                "description": entry.get("summary", entry.get("description", "")),
                "audio_url": audio_url,
                "published": entry.get("published", ""),
                "duration": entry.get("duration", ""),
                "link": entry.get("link", ""),
            }

            if audio_url:  # 音声URLがある場合のみ追加
                episodes.append(episode_info)

        # 最終取得時刻を更新
        doc_ref.update({"last_fetched": datetime.utcnow()})

        return jsonify(
            {"podcast_info": subscription_data["podcast_info"], "episodes": episodes}
        )

    except Exception as e:
        print(f"Get subscription episodes error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/favorites", methods=["POST"])
@auth_required
def add_to_favorites():
    """エピソードをお気に入りに追加"""
    try:
        user_uid = get_user_from_token()
        data = request.get_json()

        episode_id = data.get("episode_id")
        episode_info = data.get("episode_info", {})

        if not episode_id:
            return jsonify({"error": "エピソードIDが必要です"}), 400

        # 重複チェック
        favorites_ref = db.collection("favorites")
        existing = (
            favorites_ref.where("user_uid", "==", user_uid)
            .where("episode_id", "==", episode_id)
            .limit(1)
            .get()
        )

        if existing:
            return jsonify({"error": "既にお気に入りに追加済みです"}), 409

        # お気に入りに追加
        favorite_data = {
            "user_uid": user_uid,
            "episode_id": episode_id,
            "episode_info": episode_info,
            "added_at": datetime.utcnow(),
        }

        doc_ref = favorites_ref.add(favorite_data)

        return jsonify(
            {"message": "お気に入りに追加しました", "favorite_id": doc_ref[1].id}
        )

    except Exception as e:
        print(f"Add favorite error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/favorites", methods=["GET"])
@auth_required
def get_favorites():
    """ユーザーのお気に入り一覧を取得"""
    try:
        user_uid = get_user_from_token()

        favorites_ref = db.collection("favorites")
        favorites = (
            favorites_ref.where("user_uid", "==", user_uid)
            .order_by("added_at", direction=firestore.Query.DESCENDING)
            .get()
        )

        result = []
        for doc in favorites:
            data = doc.to_dict()
            favorite_info = {
                "favorite_id": doc.id,
                "episode_id": data["episode_id"],
                "episode_info": data["episode_info"],
                "added_at": (
                    data["added_at"].isoformat() if data.get("added_at") else None
                ),
            }
            result.append(favorite_info)

        return jsonify({"favorites": result})

    except Exception as e:
        print(f"Get favorites error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/favorites/<favorite_id>", methods=["DELETE"])
@auth_required
def remove_from_favorites(favorite_id):
    """お気に入りから削除"""
    try:
        user_uid = get_user_from_token()

        doc_ref = db.collection("favorites").document(favorite_id)
        doc = doc_ref.get()

        if not doc.exists:
            return jsonify({"error": "お気に入りが見つかりません"}), 404

        favorite_data = doc.to_dict()
        if favorite_data["user_uid"] != user_uid:
            return jsonify({"error": "権限がありません"}), 403

        # お気に入りを削除
        doc_ref.delete()

        return jsonify({"message": "お気に入りから削除しました"})

    except Exception as e:
        print(f"Remove favorite error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/playback-history", methods=["POST"])
@auth_required
def record_playback():
    """再生履歴を記録"""
    try:
        user_uid = get_user_from_token()
        data = request.get_json()

        episode_id = data.get("episode_id")
        episode_info = data.get("episode_info", {})
        progress = data.get("progress", 0)  # 再生位置（秒）
        duration = data.get("duration", 0)  # 総時間（秒）

        if not episode_id:
            return jsonify({"error": "エピソードIDが必要です"}), 400

        # 既存の再生履歴をチェック
        history_ref = db.collection("playback_history")
        existing = (
            history_ref.where("user_uid", "==", user_uid)
            .where("episode_id", "==", episode_id)
            .limit(1)
            .get()
        )

        playback_data = {
            "user_uid": user_uid,
            "episode_id": episode_id,
            "episode_info": episode_info,
            "progress": progress,
            "duration": duration,
            "completed": (
                progress >= duration * 0.9 if duration > 0 else False
            ),  # 90%以上で完了とみなす
            "last_played": datetime.utcnow(),
        }

        if existing:
            # 既存の履歴を更新
            doc_ref = existing[0].reference
            doc_ref.update(playback_data)
            playback_id = existing[0].id
        else:
            # 新規履歴を作成
            playback_data["first_played"] = datetime.utcnow()
            doc_ref = history_ref.add(playback_data)
            playback_id = doc_ref[1].id

        return jsonify(
            {"message": "再生履歴を記録しました", "playback_id": playback_id}
        )

    except Exception as e:
        print(f"Record playback error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/playback-history", methods=["GET"])
@auth_required
def get_playback_history():
    """ユーザーの再生履歴を取得"""
    try:
        user_uid = get_user_from_token()
        limit = int(request.args.get("limit", 50))

        history_ref = db.collection("playback_history")
        history = (
            history_ref.where("user_uid", "==", user_uid)
            .order_by("last_played", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .get()
        )

        result = []
        for doc in history:
            data = doc.to_dict()
            history_info = {
                "playback_id": doc.id,
                "episode_id": data["episode_id"],
                "episode_info": data["episode_info"],
                "progress": data.get("progress", 0),
                "duration": data.get("duration", 0),
                "completed": data.get("completed", False),
                "first_played": (
                    data["first_played"].isoformat()
                    if data.get("first_played")
                    else None
                ),
                "last_played": (
                    data["last_played"].isoformat() if data.get("last_played") else None
                ),
            }
            result.append(history_info)

        return jsonify({"history": result})

    except Exception as e:
        print(f"Get playback history error: {e}")
        return jsonify({"error": "サーバーエラーが発生しました"}), 500


@app.route("/api/podcasts/download", methods=["POST"])
@auth_required
def download_podcast_episode():
    """ポッドキャストエピソードをダウンロードしてライブラリに追加"""
    try:
        user_uid = request.user["uid"]
        data = request.json

        episode_id = data.get("episode_id")
        audio_url = data.get("audio_url")
        title = data.get("title", "Untitled Episode")
        description = data.get("description", "")
        podcast_name = data.get("podcast_name", "Unknown Podcast")

        if not audio_url:
            return jsonify({"error": "Audio URL is required"}), 400

        app.logger.info(f"📥 Downloading podcast episode: {title}")

        # 音声ファイルをダウンロード
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AIIV-Podcast-Downloader/1.0)"
        }
        response = requests.get(audio_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()

        # ファイル形式を判定
        content_type = response.headers.get("content-type", "")
        if "audio/mpeg" in content_type or audio_url.endswith(".mp3"):
            file_extension = "mp3"
        elif "audio/mp4" in content_type or audio_url.endswith(".m4a"):
            file_extension = "m4a"
        elif "audio/wav" in content_type or audio_url.endswith(".wav"):
            file_extension = "wav"
        else:
            file_extension = "mp3"  # デフォルト

        # 一意のファイル名を生成
        safe_title = re.sub(r"[^\w\s-]", "", title)[:50]
        timestamp = int(time.time())
        filename = f"podcast_{safe_title}_{timestamp}.{file_extension}"

        # Google Cloud Storageにアップロード
        bucket_name = os.environ.get("GCS_BUCKET_AUDIO", "ai-fm-audio")
        bucket = storage_client.bucket(bucket_name)

        # オブジェクト名を生成
        object_name = f"podcasts/{user_uid}/{filename}"
        blob = bucket.blob(object_name)

        # メタデータを設定
        blob.metadata = {
            "title": title,
            "podcast_name": podcast_name,
            "original_url": audio_url,
            "downloaded_at": datetime.utcnow().isoformat(),
            "episode_id": episode_id,
        }

        # ファイルをアップロード
        blob.upload_from_string(
            response.content, content_type=f"audio/{file_extension}"
        )

        # 再生用のSigned URLを生成
        play_url = blob.generate_signed_url(
            version="v4", expiration=timedelta(hours=1), method="GET"
        )

        # Firestoreにトラック情報を保存
        track_data = {
            "title": title,
            "artist": podcast_name,
            "description": description,
            "filename": filename,
            "objectName": object_name,
            "contentType": f"audio/{file_extension}",
            "uploadedAt": datetime.utcnow(),
            "createdBy": user_uid,
            "duration": 0,  # 実際の長さは後で更新可能
            "fileSize": len(response.content),
            "isPodcast": True,
            "podcastEpisodeId": episode_id,
            "originalUrl": audio_url,
            "downloadedFrom": "podcast_search",
        }

        # Firestoreに保存
        track_ref = db.collection("tracks").add(track_data)
        track_id = track_ref[1].id

        app.logger.info(f"✅ Podcast episode downloaded and saved as track: {track_id}")

        return jsonify(
            {
                "message": "Podcast episode downloaded successfully",
                "track_id": track_id,
                "title": title,
                "podcast_name": podcast_name,
                "play_url": play_url,
            }
        )

    except Exception as e:
        app.logger.error(f"❌ Download podcast episode error: {e}")
        return jsonify({"error": "Failed to download episode", "details": str(e)}), 500


@app.route("/api/debug/tracks-count-no-auth", methods=["GET"])
def debug_tracks_count_no_auth():
    """デバッグ用: 認証不要でFirestoreのトラック数確認"""
    try:
        if db is None:
            return jsonify({"error": "Firestore not available", "count": 0}), 503

        # 全トラック数をカウント（開発用）
        all_tracks = db.collection("tracks").get()

        tracks_info = []
        for track in all_tracks:
            track_data = track.to_dict()
            tracks_info.append(
                {
                    "trackId": track.id,
                    "title": track_data.get("title", "N/A"),
                    "uploaderUid": track_data.get("uploaderUid", "N/A"),
                    "createdAt": track_data.get("createdAt", "N/A"),
                    "status": track_data.get("status", "N/A"),
                }
            )

        return jsonify(
            {
                "firestoreStatus": "connected",
                "totalTracks": len(tracks_info),
                "tracks": tracks_info,
                "note": "No auth required - development only",
            }
        )

    except Exception as e:
        return jsonify({"error": str(e), "firestoreStatus": "error"}), 500


@app.route("/api/debug/tracks-count", methods=["GET"])
@verify_token
def debug_tracks_count():
    """デバッグ用: Firestoreのトラック数確認"""
    try:
        if db is None:
            return jsonify({"error": "Firestore not available", "count": 0}), 503

        # 現在のユーザーのトラック数をカウント
        current_user_uid = request.user_uid
        user_tracks = (
            db.collection("tracks").where("uploaderUid", "==", current_user_uid).get()
        )

        tracks_info = []
        for track in user_tracks:
            track_data = track.to_dict()
            tracks_info.append(
                {
                    "trackId": track.id,
                    "title": track_data.get("title", "N/A"),
                    "createdAt": track_data.get("createdAt", "N/A"),
                    "status": track_data.get("status", "N/A"),
                }
            )

        return jsonify(
            {
                "firestoreStatus": "connected",
                "userUid": current_user_uid,
                "totalTracks": len(tracks_info),
                "tracks": tracks_info,
            }
        )

    except Exception as e:
        app.logger.error(f"Debug tracks count error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/debug/auth-status", methods=["GET"])
def debug_auth_status():
    """認証不要のデバッグ用: 認証状態確認"""
    try:
        # リクエストヘッダーの確認
        auth_header = request.headers.get("Authorization", "None")

        # 基本的な情報を返す
        return jsonify(
            {
                "authHeader": (
                    auth_header[:50] + "..." if len(auth_header) > 50 else auth_header
                ),
                "hasAuthHeader": auth_header != "None",
                "firestoreStatus": "connected" if db is not None else "disconnected",
                "serverTime": datetime.utcnow().isoformat(),
                "message": "This endpoint does not require authentication",
            }
        )

    except Exception as e:
        app.logger.error(f"Debug auth status error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/clear-orphaned-tracks", methods=["POST"])
@verify_token
def clear_orphaned_tracks():
    """既存のIDが紐づいていない可能性があるトラックをすべて削除（UI操作じゃない方法）"""
    try:
        user_uid = request.user_uid
        app.logger.info(f"Starting orphaned tracks cleanup for user: {user_uid}")

        # ユーザーのライブラリドキュメントを取得
        user_library_ref = db.collection("user_libraries").document(user_uid)
        user_library_doc = user_library_ref.get()

        if not user_library_doc.exists:
            return jsonify({"message": "No user library found", "removedTracks": []})

        library_data = user_library_doc.to_dict()
        saved_tracks = library_data.get("savedTracks", [])

        if not saved_tracks:
            return jsonify(
                {"message": "No tracks in user library", "removedTracks": []}
            )

        orphaned_tracks = []
        valid_tracks = []

        app.logger.info(f"Checking {len(saved_tracks)} tracks for orphaned references")

        # 各トラックIDの存在を確認
        for track_id in saved_tracks:
            try:
                track_doc = db.collection("tracks").document(track_id).get()
                if track_doc.exists:
                    valid_tracks.append(track_id)
                    app.logger.debug(f"Valid track found: {track_id}")
                else:
                    orphaned_tracks.append(track_id)
                    app.logger.info(f"Orphaned track reference found: {track_id}")
            except Exception as e:
                app.logger.error(f"Error checking track {track_id}: {e}")
                orphaned_tracks.append(track_id)

        # 孤立したトラック参照を削除
        if orphaned_tracks:
            user_library_ref.update(
                {"savedTracks": valid_tracks, "updatedAt": datetime.utcnow()}
            )

            app.logger.info(
                f"Removed {len(orphaned_tracks)} orphaned track references: {orphaned_tracks}"
            )

            return jsonify(
                {
                    "message": f"Removed {len(orphaned_tracks)} orphaned track references",
                    "removedTracks": orphaned_tracks,
                    "validTracks": valid_tracks,
                    "totalProcessed": len(saved_tracks),
                }
            )
        else:
            return jsonify(
                {
                    "message": "No orphaned tracks found",
                    "removedTracks": [],
                    "validTracks": valid_tracks,
                    "totalProcessed": len(saved_tracks),
                }
            )

    except Exception as e:
        app.logger.error(f"Failed to clear orphaned tracks: {e}")
        return jsonify({"error": "Failed to clear orphaned tracks"}), 500


@app.route("/api/admin/clear-orphaned-tracks-direct/<user_uid>", methods=["POST"])
def clear_orphaned_tracks_direct(user_uid):
    """認証なしでユーザーUIDを指定して孤立トラック参照を削除（緊急用）"""
    try:
        app.logger.info(f"Direct orphaned tracks cleanup for user: {user_uid}")

        # ユーザーのライブラリドキュメントを取得
        user_library_ref = db.collection("user_libraries").document(user_uid)
        user_library_doc = user_library_ref.get()

        if not user_library_doc.exists:
            return jsonify(
                {
                    "message": "No user library found",
                    "removedTracks": [],
                    "userUid": user_uid,
                }
            )

        library_data = user_library_doc.to_dict()
        saved_tracks = library_data.get("savedTracks", [])

        if not saved_tracks:
            return jsonify(
                {
                    "message": "No tracks in user library",
                    "removedTracks": [],
                    "userUid": user_uid,
                }
            )

        orphaned_tracks = []
        valid_tracks = []

        app.logger.info(f"Checking {len(saved_tracks)} tracks for orphaned references")

        # 各トラックIDの存在を確認
        for track_id in saved_tracks:
            try:
                track_doc = db.collection("tracks").document(track_id).get()
                if track_doc.exists:
                    valid_tracks.append(track_id)
                    app.logger.debug(f"Valid track found: {track_id}")
                else:
                    orphaned_tracks.append(track_id)
                    app.logger.info(f"Orphaned track reference found: {track_id}")
            except Exception as e:
                app.logger.error(f"Error checking track {track_id}: {e}")
                orphaned_tracks.append(track_id)

        # 孤立したトラック参照を削除
        if orphaned_tracks:
            user_library_ref.update(
                {"savedTracks": valid_tracks, "updatedAt": datetime.utcnow()}
            )

            app.logger.info(
                f"Removed {len(orphaned_tracks)} orphaned track references: {orphaned_tracks}"
            )

            return jsonify(
                {
                    "message": f"Removed {len(orphaned_tracks)} orphaned track references",
                    "removedTracks": orphaned_tracks,
                    "validTracks": valid_tracks,
                    "totalProcessed": len(saved_tracks),
                    "userUid": user_uid,
                }
            )
        else:
            return jsonify(
                {
                    "message": "No orphaned tracks found",
                    "removedTracks": [],
                    "validTracks": valid_tracks,
                    "totalProcessed": len(saved_tracks),
                    "userUid": user_uid,
                }
            )

    except Exception as e:
        app.logger.error(f"Failed to clear orphaned tracks for {user_uid}: {e}")
        return (
            jsonify({"error": "Failed to clear orphaned tracks", "userUid": user_uid}),
            500,
        )


# Podcast Library API Endpoints
@app.route("/api/podcast-library/add", methods=["POST"])
@verify_token
def add_to_podcast_library():
    """Add episode to user's podcast library"""
    try:
        data = request.json
        episode_id = data.get("episodeId")
        title = data.get("title", "")
        description = data.get("description", "")
        added_at = data.get("addedAt", datetime.utcnow().isoformat())

        if not episode_id:
            return jsonify({"error": "Episode ID is required"}), 400

        user_uid = request.user_uid

        # Check if episode is already in podcast library
        podcast_library_ref = db.collection("podcast_library").document(user_uid)
        podcast_library_doc = podcast_library_ref.get()

        if podcast_library_doc.exists:
            saved_episodes = podcast_library_doc.to_dict().get("episodes", [])

            # Check if episode already exists
            for episode in saved_episodes:
                if episode.get("episodeId") == episode_id:
                    return jsonify({"error": "Episode already in podcast library"}), 409

            # Add new episode
            saved_episodes.append(
                {
                    "episodeId": episode_id,
                    "title": title,
                    "description": description,
                    "addedAt": added_at,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

            podcast_library_ref.update(
                {
                    "episodes": saved_episodes,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            # Create new podcast library document
            podcast_library_ref.set(
                {
                    "user_uid": user_uid,
                    "episodes": [
                        {
                            "episodeId": episode_id,
                            "title": title,
                            "description": description,
                            "addedAt": added_at,
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    ],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )

        app.logger.info(
            f"Added episode {episode_id} to podcast library for user {user_uid}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Episode added to podcast library",
                "episodeId": episode_id,
                "title": title,
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to add episode to podcast library: {e}")
        return jsonify({"error": "Failed to add to podcast library"}), 500


@app.route("/api/podcast-library", methods=["GET"])
@verify_token
def get_podcast_library():
    """Get user's podcast library"""
    try:
        user_uid = request.user_uid
        view = request.args.get(
            "view", "episodes"
        )  # episodes, podcasts, playlists, settings

        podcast_library_ref = db.collection("podcast_library").document(user_uid)
        podcast_library_doc = podcast_library_ref.get()

        if not podcast_library_doc.exists:
            return jsonify({"items": [], "view": view, "total": 0})

        library_data = podcast_library_doc.to_dict()
        episodes = library_data.get("episodes", [])

        # Sort by added date (most recent first)
        episodes.sort(key=lambda x: x.get("addedAt", ""), reverse=True)

        return jsonify(
            {
                "items": episodes,
                "view": view,
                "total": len(episodes),
                "updated_at": library_data.get("updated_at"),
            }
        )

    except Exception as e:
        app.logger.error(
            f"Failed to get podcast library for user {request.user_uid}: {e}"
        )
        return jsonify({"error": "Failed to get podcast library"}), 500


@app.route("/api/podcast-library/<episode_id>", methods=["DELETE"])
@verify_token
def remove_from_podcast_library(episode_id):
    """Remove episode from user's podcast library"""
    try:
        user_uid = request.user_uid

        podcast_library_ref = db.collection("podcast_library").document(user_uid)
        podcast_library_doc = podcast_library_ref.get()

        if not podcast_library_doc.exists:
            return jsonify({"error": "Podcast library not found"}), 404

        library_data = podcast_library_doc.to_dict()
        episodes = library_data.get("episodes", [])

        # Find and remove the episode
        episode_title = None
        updated_episodes = []
        for episode in episodes:
            if episode.get("episodeId") == episode_id:
                episode_title = episode.get("title", "Unknown Episode")
            else:
                updated_episodes.append(episode)

        if episode_title is None:
            return jsonify({"error": "Episode not found in podcast library"}), 404

        # Update the podcast library
        podcast_library_ref.update(
            {"episodes": updated_episodes, "updated_at": datetime.utcnow().isoformat()}
        )

        app.logger.info(
            f"Removed episode {episode_id} from podcast library for user {user_uid}"
        )

        return jsonify(
            {
                "success": True,
                "message": "Episode removed from podcast library",
                "episodeId": episode_id,
                "title": episode_title,
            }
        )

    except Exception as e:
        app.logger.error(f"Failed to remove episode from podcast library: {e}")
        return jsonify({"error": "Failed to remove from podcast library"}), 500


# ============== PODCAST PLAYLIST ENDPOINTS ==============


@app.route("/api/podcast-playlists", methods=["GET"])
@verify_token
def get_podcast_playlists():
    """Get all podcast playlists for the user"""
    try:
        user_uid = request.user_uid

        playlists_ref = db.collection("podcast_playlists").where(
            "user_uid", "==", user_uid
        )
        playlists_docs = playlists_ref.get()

        playlists = []
        for doc in playlists_docs:
            playlist_data = doc.to_dict()
            playlist_data["id"] = doc.id
            playlists.append(playlist_data)

        # Sort by creation date (newest first)
        playlists.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jsonify({"playlists": playlists, "count": len(playlists)})

    except Exception as e:
        app.logger.error(
            f"Failed to get podcast playlists for user {request.user_uid}: {e}"
        )
        return jsonify({"error": "Failed to get podcast playlists"}), 500


@app.route("/api/podcast-playlists", methods=["POST"])
@verify_token
def create_podcast_playlist():
    """Create a new podcast playlist"""
    try:
        user_uid = request.user_uid
        data = request.get_json()

        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "Playlist name is required"}), 400

        description = data.get("description", "").strip()
        emoji = data.get("emoji", "🎙️")

        playlist_data = {
            "user_uid": user_uid,
            "name": name,
            "description": description,
            "emoji": emoji,
            "episodes": [],  # Array of episode objects
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Add to Firestore
        playlist_ref = db.collection("podcast_playlists").add(playlist_data)
        playlist_id = playlist_ref[1].id

        playlist_data["id"] = playlist_id

        return (
            jsonify(
                {
                    "message": "Podcast playlist created successfully",
                    "playlist": playlist_data,
                }
            ),
            201,
        )

    except Exception as e:
        app.logger.error(
            f"Failed to create podcast playlist for user {request.user_uid}: {e}"
        )
        return jsonify({"error": "Failed to create podcast playlist"}), 500


@app.route("/api/podcast-playlists/<playlist_id>", methods=["GET"])
@verify_token
def get_podcast_playlist(playlist_id):
    """Get a specific podcast playlist"""
    try:
        user_uid = request.user_uid

        playlist_doc = db.collection("podcast_playlists").document(playlist_id).get()

        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()

        # Check if user owns this playlist
        if playlist_data.get("user_uid") != user_uid:
            return jsonify({"error": "Access denied"}), 403

        playlist_data["id"] = playlist_doc.id

        return jsonify({"playlist": playlist_data})

    except Exception as e:
        app.logger.error(f"Failed to get podcast playlist {playlist_id}: {e}")
        return jsonify({"error": "Failed to get podcast playlist"}), 500


@app.route("/api/podcast-playlists/<playlist_id>", methods=["DELETE"])
@verify_token
def delete_podcast_playlist(playlist_id):
    """Delete a podcast playlist"""
    try:
        user_uid = request.user_uid

        playlist_doc = db.collection("podcast_playlists").document(playlist_id).get()

        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()

        # Check if user owns this playlist
        if playlist_data.get("user_uid") != user_uid:
            return jsonify({"error": "Access denied"}), 403

        # Delete the playlist
        db.collection("podcast_playlists").document(playlist_id).delete()

        return jsonify({"message": "Podcast playlist deleted successfully"})

    except Exception as e:
        app.logger.error(f"Failed to delete podcast playlist {playlist_id}: {e}")
        return jsonify({"error": "Failed to delete podcast playlist"}), 500


@app.route("/api/podcast-playlists/<playlist_id>/episodes", methods=["POST"])
@verify_token
def add_episode_to_podcast_playlist(playlist_id):
    """Add an episode to a podcast playlist"""
    try:
        user_uid = request.user_uid
        data = request.get_json()

        episode_id = data.get("episode_id")
        if not episode_id:
            return jsonify({"error": "Episode ID is required"}), 400

        playlist_ref = db.collection("podcast_playlists").document(playlist_id)
        playlist_doc = playlist_ref.get()

        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()

        # Check if user owns this playlist
        if playlist_data.get("user_uid") != user_uid:
            return jsonify({"error": "Access denied"}), 403

        episodes = playlist_data.get("episodes", [])

        # Check if episode already exists
        if any(ep.get("id") == episode_id for ep in episodes):
            return jsonify({"error": "Episode already exists in playlist"}), 409

        # For now, we'll store just the episode ID
        # In a real app, you might want to fetch episode details and store them
        episode_data = {"id": episode_id, "added_at": datetime.utcnow().isoformat()}

        episodes.append(episode_data)

        # Update the playlist
        playlist_ref.update(
            {"episodes": episodes, "updated_at": datetime.utcnow().isoformat()}
        )

        return jsonify({"message": "Episode added to podcast playlist successfully"})

    except Exception as e:
        app.logger.error(
            f"Failed to add episode to podcast playlist {playlist_id}: {e}"
        )
        return jsonify({"error": "Failed to add episode to playlist"}), 500


@app.route(
    "/api/podcast-playlists/<playlist_id>/episodes/<episode_id>", methods=["DELETE"]
)
@verify_token
def remove_episode_from_podcast_playlist(playlist_id, episode_id):
    """Remove an episode from a podcast playlist"""
    try:
        user_uid = request.user_uid

        playlist_ref = db.collection("podcast_playlists").document(playlist_id)
        playlist_doc = playlist_ref.get()

        if not playlist_doc.exists:
            return jsonify({"error": "Playlist not found"}), 404

        playlist_data = playlist_doc.to_dict()

        # Check if user owns this playlist
        if playlist_data.get("user_uid") != user_uid:
            return jsonify({"error": "Access denied"}), 403

        episodes = playlist_data.get("episodes", [])

        # Remove the episode
        episodes = [ep for ep in episodes if ep.get("id") != episode_id]

        # Update the playlist
        playlist_ref.update(
            {"episodes": episodes, "updated_at": datetime.utcnow().isoformat()}
        )

        return jsonify(
            {"message": "Episode removed from podcast playlist successfully"}
        )

    except Exception as e:
        app.logger.error(
            f"Failed to remove episode from podcast playlist {playlist_id}: {e}"
        )
        return jsonify({"error": "Failed to remove episode from playlist"}), 500


# ============== END PODCAST PLAYLIST ENDPOINTS ==============

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
