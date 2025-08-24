-- Create database for podcast episodes
CREATE DATABASE podcast_episodes;

-- Create episodes table
\c podcast_episodes;

CREATE TABLE IF NOT EXISTS episodes (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    date VARCHAR(10) NOT NULL,
    duration_sec INTEGER DEFAULT 0,
    tags JSON,
    guests JSON,
    audio_url VARCHAR(500) NOT NULL,
    filename VARCHAR(100) NOT NULL,
    storage VARCHAR(10) DEFAULT 'local',
    source VARCHAR(20) DEFAULT 'upload',
    original_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_episodes_created_at ON episodes(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodes_source ON episodes(source);