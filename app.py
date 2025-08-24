from flask import Flask, send_file, jsonify, request, redirect, url_for
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import uuid
import subprocess
import tempfile
import re
from google.cloud import storage
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSON

app = Flask(__name__)

# Application version
APP_VERSION = "v2.0.2"

# Database configuration
# Default to local SQLite for development, PostgreSQL for production
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///episodes.db')

if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Episode model
class Episode(db.Model):
    __tablename__ = 'episodes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD format
    duration_sec = db.Column(db.Integer, default=0)
    tags = db.Column(JSON)  # Array of strings
    guests = db.Column(JSON)  # Array of strings
    audio_url = db.Column(db.String(500), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    storage = db.Column(db.String(10), default='local')  # 'gcs' or 'local'
    source = db.Column(db.String(20), default='upload')  # 'upload' or 'youtube'
    original_url = db.Column(db.String(500))  # For YouTube sources
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'durationSec': self.duration_sec,
            'tags': self.tags or [],
            'guests': self.guests or [],
            'audioUrl': self.audio_url,
            'filename': self.filename,
            'storage': self.storage,
            'source': self.source,
            'originalUrl': self.original_url
        }

# Initialize database
def init_db():
    """Initialize database tables"""
    try:
        with app.app_context():
            db.create_all()
            print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

# Call init_db when app starts
init_db()

@app.route('/')
def serve_index():
    return send_file('index.html', mimetype='text/html')

# Configuration
UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a'}

# Check if yt-dlp or youtube-dl is available
def check_youtube_downloader():
    """Check if YouTube downloader is available"""
    try:
        subprocess.run(['yt-dlp', '--version'], capture_output=True, check=True)
        return 'yt-dlp'
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(['youtube-dl', '--version'], capture_output=True, check=True)
            return 'youtube-dl'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None
EPISODES_FILE = 'episodes.json'
GCS_BUCKET_NAME = 'podcast-homepage-audio'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Initialize Google Cloud Storage
try:
    storage_client = storage.Client()
    bucket = storage_client.bucket(GCS_BUCKET_NAME)
except Exception as e:
    print(f"Warning: Could not initialize Google Cloud Storage: {e}")
    storage_client = None
    bucket = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_gcs(file_path, destination_filename):
    """Upload file to Google Cloud Storage"""
    if not storage_client or not bucket:
        return None
    
    try:
        blob = bucket.blob(destination_filename)
        blob.upload_from_filename(file_path)
        
        # Make the blob publicly readable
        blob.make_public()
        
        return blob.public_url
    except Exception as e:
        print(f"Error uploading to GCS: {e}")
        return None

def delete_from_gcs(filename):
    """Delete file from Google Cloud Storage"""
    if not storage_client or not bucket:
        return False
    
    try:
        blob = bucket.blob(filename)
        blob.delete()
        return True
    except Exception as e:
        print(f"Error deleting from GCS: {e}")
        return False

def load_episodes():
    """Load episodes from database"""
    try:
        episodes = Episode.query.order_by(Episode.created_at.desc()).all()
        return [ep.to_dict() for ep in episodes]
    except Exception as e:
        print(f"Database error: {e}")
        # Fallback to file-based storage if database fails
        if os.path.exists(EPISODES_FILE):
            with open(EPISODES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

def save_episodes(episodes):
    """Save episodes to JSON file (legacy support)"""
    with open(EPISODES_FILE, 'w', encoding='utf-8') as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)

def create_episode_db(title, description, date, tags, guests, audio_url, filename, storage='local', source='upload', original_url=None):
    """Create new episode in database"""
    try:
        episode = Episode(
            title=title,
            description=description,
            date=date,
            tags=tags,
            guests=guests,
            audio_url=audio_url,
            filename=filename,
            storage=storage,
            source=source,
            original_url=original_url
        )
        db.session.add(episode)
        db.session.commit()
        return episode.to_dict()
    except Exception as e:
        db.session.rollback()
        print(f"Database error creating episode: {e}")
        return None

def delete_episode_db(episode_id):
    """Delete episode from database"""
    try:
        episode = Episode.query.get(episode_id)
        if episode:
            episode_data = episode.to_dict()
            db.session.delete(episode)
            db.session.commit()
            return episode_data
        return None
    except Exception as e:
        db.session.rollback()
        print(f"Database error deleting episode: {e}")
        return None

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "app": "podcast-homepage", "version": APP_VERSION})

@app.route('/api/version')
def get_version():
    return jsonify({"version": APP_VERSION, "app": "Podcast Homepage"})

@app.route('/api/episodes')
def get_episodes():
    """Get all episodes"""
    episodes = load_episodes()
    return jsonify(episodes)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload audio file and create episode"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed: mp3, wav, ogg, m4a'}), 400
    
    # Get episode metadata
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    tags = request.form.get('tags', '').split(',') if request.form.get('tags') else []
    guests = request.form.get('guests', '').split(',') if request.form.get('guests') else []
    
    if not title:
        return jsonify({'error': 'Title is required'}), 400
    
    # Generate unique filename
    file_extension = file.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        # Save file temporarily
        file.save(file_path)
        
        # Upload to Google Cloud Storage
        gcs_url = upload_to_gcs(file_path, unique_filename)
        
        if gcs_url:
            audio_url = gcs_url
            storage_type = 'gcs'
            # Clean up temporary file
            os.remove(file_path)
        else:
            # Fallback: move to local audio directory
            audio_path = os.path.join(AUDIO_FOLDER, unique_filename)
            os.rename(file_path, audio_path)
            audio_url = f'/audio/{unique_filename}'
            storage_type = 'local'
        
        # Create episode in database
        new_episode = create_episode_db(
            title=title.strip(),
            description=description.strip(),
            date=datetime.now().strftime('%Y-%m-%d'),
            tags=[tag.strip() for tag in tags if tag.strip()],
            guests=[guest.strip() for guest in guests if guest.strip()],
            audio_url=audio_url,
            filename=unique_filename,
            storage=storage_type,
            source='upload'
        )
        
        if not new_episode:
            return jsonify({'error': 'Failed to save episode to database'}), 500
        
        return jsonify({'success': True, 'episode': new_episode})
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """Serve audio files"""
    return send_from_directory(AUDIO_FOLDER, filename)

@app.route('/api/episodes/<int:episode_id>', methods=['DELETE'])
def delete_episode(episode_id):
    """Delete an episode"""
    episode_to_delete = delete_episode_db(episode_id)
    
    if not episode_to_delete:
        return jsonify({'error': 'Episode not found'}), 404
    
    # Delete audio file if it exists
    if 'filename' in episode_to_delete:
        if episode_to_delete.get('storage') == 'gcs':
            # Delete from Google Cloud Storage
            delete_from_gcs(episode_to_delete['filename'])
        else:
            # Delete from local storage
            audio_path = os.path.join(AUDIO_FOLDER, episode_to_delete['filename'])
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    save_episodes(episodes)
    return jsonify({'success': True})

@app.route('/api/youtube', methods=['POST'])
def download_from_youtube():
    """Download audio from YouTube URL"""
    data = request.get_json()
    youtube_url = data.get('url', '').strip()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    tags = data.get('tags', [])
    guests = data.get('guests', [])
    
    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400
    
    # Validate and normalize YouTube URL
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = youtube_regex.match(youtube_url)
    if not match:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Extract video ID and create clean URL
    video_id = match.group(6)
    if video_id:
        # Use clean YouTube URL to avoid playlist issues
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    
    try:
        # Generate unique filename
        unique_id = uuid.uuid4().hex
        unique_filename = f"{unique_id}.mp3"
        temp_audio_file = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Use yt-dlp to download audio (fallback to youtube-dl if not available)
        import shutil
        
        # Find yt-dlp or youtube-dl command
        yt_command = None
        if shutil.which('yt-dlp'):
            yt_command = 'yt-dlp'
        elif shutil.which('youtube-dl'):
            yt_command = 'youtube-dl'
        else:
            # Try common Windows paths
            import platform
            if platform.system() == 'Windows':
                common_paths = [
                    r'C:\Users\Tenormusica\AppData\Local\Programs\Python\Python310\Scripts\yt-dlp.exe',
                    r'C:\Python310\Scripts\yt-dlp.exe',
                    r'C:\Python39\Scripts\yt-dlp.exe',
                    r'C:\Python38\Scripts\yt-dlp.exe',
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        yt_command = path
                        break
        
        if not yt_command:
            return jsonify({'error': 'YouTube downloader (yt-dlp or youtube-dl) not found. Please install yt-dlp.'}), 500
        
        try:
            # Download audio with found command and bot detection countermeasures
            subprocess.run([
                yt_command,
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', temp_audio_file.replace('.mp3', '.%(ext)s'),
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                '--referer', 'https://www.youtube.com/',
                '--no-check-certificate',
                '--prefer-free-formats',
                '--no-warnings',
                '--quiet',
                '--no-playlist',
                youtube_url
            ], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            # Try alternative approach if first attempt fails
            try:
                print(f"First attempt failed, trying alternative method: {error_msg}")
                # Use more conservative settings
                subprocess.run([
                    yt_command,
                    '--extract-audio',
                    '--audio-format', 'mp3',
                    '--audio-quality', '0',
                    '--output', temp_audio_file.replace('.mp3', '.%(ext)s'),
                    '--user-agent', 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                    '--sleep-interval', '2',
                    '--max-sleep-interval', '5',
                    '--no-check-certificate',
                    '--ignore-errors',
                    '--no-playlist',
                    youtube_url
                ], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e2:
                error_msg2 = e2.stderr if e2.stderr else str(e2)
                return jsonify({'error': f'YouTube download failed after retry. Primary error: {error_msg}. Retry error: {error_msg2}. This might be due to YouTube bot detection. Please try a different video or try again later.'}), 500
        
        # Check if file was created
        if not os.path.exists(temp_audio_file):
            return jsonify({'error': 'Failed to download audio from YouTube'}), 500
        
        # Upload to Google Cloud Storage
        gcs_url = upload_to_gcs(temp_audio_file, unique_filename)
        
        if gcs_url:
            audio_url = gcs_url
            storage_type = 'gcs'
            # Clean up temporary file
            os.remove(temp_audio_file)
        else:
            # Fallback: move to local audio directory
            audio_path = os.path.join(AUDIO_FOLDER, unique_filename)
            os.rename(temp_audio_file, audio_path)
            audio_url = f'/audio/{unique_filename}'
            storage_type = 'local'
        
        # Get video metadata if title not provided
        if not title:
            try:
                result = subprocess.run([
                    yt_command, 
                    '--get-title', 
                    '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    '--no-check-certificate',
                    '--quiet',
                    youtube_url
                ], capture_output=True, text=True, check=True)
                title = result.stdout.strip()
            except Exception as e:
                print(f"Failed to get video title: {e}")
                title = f"YouTube Episode - {unique_id[:8]}"
        
        # Create episode in database
        new_episode = create_episode_db(
            title=title,
            description=description or f"Downloaded from YouTube: {youtube_url}",
            date=datetime.now().strftime('%Y-%m-%d'),
            tags=tags if isinstance(tags, list) else [],
            guests=guests if isinstance(guests, list) else [],
            audio_url=audio_url,
            filename=unique_filename,
            storage=storage_type,
            source='youtube',
            original_url=youtube_url
        )
        
        if not new_episode:
            return jsonify({'error': 'Failed to save episode to database'}), 500
        
        return jsonify({'success': True, 'episode': new_episode})
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'YouTube download failed: {e.stderr}'}), 500
    except Exception as e:
        return jsonify({'error': f'YouTube download failed: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)