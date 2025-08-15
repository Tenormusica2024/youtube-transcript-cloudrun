# app_hybrid.py - YouTube Transcript Hybrid Summarizer (FastAPI)
# Client-side transcript extraction + Server-side Gemini AI summarization

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Gemini AI
import google.generativeai as genai

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN", "hybrid-yt-token-2024")
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "https://www.youtube.com,https://m.youtube.com,https://music.youtube.com",
)
PORT = int(os.getenv("PORT", 8766))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# FastAPI app
app = FastAPI(
    title="YouTube Transcript Hybrid Summarizer",
    description="Client-side transcript extraction + Server-side AI summarization",
    version="1.0.0",
)

# CORS middleware
origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")] if ALLOWED_ORIGINS else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class SummarizeRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    title: Optional[str] = Field(None, description="Video title (optional)")
    channel: Optional[str] = Field(None, description="Channel name (optional)")
    transcript: str = Field(..., description="Transcript text extracted by client")
    lang: Optional[str] = Field(
        None, description="Transcript language code (e.g., 'ja', 'en')"
    )
    target_lang: Optional[str] = Field(
        "ja", description="Target language for summary (default: Japanese)"
    )
    max_words: Optional[int] = Field(
        300, description="Target word count for summary (guideline)"
    )


class SummarizeResponse(BaseModel):
    url: str
    title: Optional[str]
    channel: Optional[str]
    original_lang: Optional[str]
    target_lang: str
    transcript_length: int
    chunks: int
    summary: str
    processing_time: float


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str


# Utility functions
def chunk_text(text: str, max_chars: int = 8000) -> List[str]:
    """Split text into manageable chunks for AI processing"""
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    # Split by lines for safety
    lines = text.splitlines()
    chunks = []
    current_chunk = []
    current_length = 0

    for line in lines:
        line_length = len(line) + 1  # +1 for newline
        if current_length + line_length > max_chars and current_chunk:
            chunks.append("\n".join(current_chunk))
            current_chunk = [line]
            current_length = line_length
        else:
            current_chunk.append(line)
            current_length += line_length

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def gemini_summarize(text: str, target_lang: str = "ja", max_words: int = 300) -> str:
    """Summarize text using Gemini AI"""
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")

        # Language-specific prompts
        if target_lang == "ja":
            prompt = (
                f"以下はYouTube動画の字幕です。重要なポイントを失わず、"
                f"日本語で約{max_words}語以内で要約してください。\n"
                f"構造: 見出し → 箇条書き → 結論の形式でまとめてください。\n\n"
                f"--- 字幕内容 ---\n{text}\n\n"
                f"--- 出力フォーマット ---\n"
                f"# 要約タイトル\n"
                f"## 主要ポイント\n"
                f"- 重要なポイント1\n"
                f"- 重要なポイント2\n"
                f"- 重要なポイント3\n\n"
                f"## 結論\n"
                f"要約の結論...\n"
            )
        else:
            prompt = (
                f"Please summarize the following YouTube video transcript in approximately {max_words} words.\n"
                f"Structure: Title → Key Points → Conclusion\n\n"
                f"--- Transcript ---\n{text}\n\n"
                f"--- Output Format ---\n"
                f"# Summary Title\n"
                f"## Key Points\n"
                f"- Key point 1\n"
                f"- Key point 2\n"
                f"- Key point 3\n\n"
                f"## Conclusion\n"
                f"Summary conclusion...\n"
            )

        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini summarization error: {e}")
        raise HTTPException(
            status_code=500, detail=f"AI summarization failed: {str(e)}"
        )


def gemini_summarize_multi(chunks: List[str], target_lang: str, max_words: int) -> str:
    """Multi-stage summarization for long transcripts"""
    try:
        # Stage 1: Summarize each chunk
        partial_summaries = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            partial = gemini_summarize(chunk, target_lang, max_words=max_words // 2)
            partial_summaries.append(f"[Part {i}/{len(chunks)}]\n{partial}")

        # Stage 2: Consolidate summaries
        model = genai.GenerativeModel("gemini-1.5-pro")

        if target_lang == "ja":
            consolidation_prompt = (
                f"以下は動画の部分要約の一覧です。"
                f"重複を除き、重要な情報を統合して、"
                f"日本語で約{max_words}語の最終要約を作成してください。\n\n"
                + "\n\n".join(partial_summaries)
            )
        else:
            consolidation_prompt = (
                f"The following are partial summaries of a video. "
                f"Please consolidate them into a final summary of approximately {max_words} words.\n\n"
                + "\n\n".join(partial_summaries)
            )

        final_response = model.generate_content(consolidation_prompt)
        return final_response.text.strip()
    except Exception as e:
        logger.error(f"Multi-stage summarization error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Multi-stage AI summarization failed: {str(e)}"
        )


# API Endpoints
@app.get("/healthz", response_model=HealthResponse)
def healthcheck():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=str(int(time.time())),
        service="YouTube Transcript Hybrid Summarizer",
    )


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(
    body: SummarizeRequest,
    authorization: Optional[str] = Header(None),
):
    """Summarize transcript text using Gemini AI"""
    import time

    start_time = time.time()

    # Simple token authentication
    if authorization != f"Bearer {API_AUTH_TOKEN}":
        logger.warning(f"Unauthorized access attempt from: {authorization}")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API token")

    # Input validation
    if len(body.transcript) < 10:
        raise HTTPException(
            status_code=400, detail="Transcript is too short (minimum 10 characters)"
        )

    if len(body.transcript) > 2_000_000:  # ~2MB limit
        raise HTTPException(
            status_code=413, detail="Transcript too large (maximum 2MB)"
        )

    logger.info(f"Processing transcript: {len(body.transcript)} chars, URL: {body.url}")

    try:
        # Split text into chunks if needed
        chunks = chunk_text(body.transcript, max_chars=8000)

        if len(chunks) == 1:
            summary = gemini_summarize(
                chunks[0],
                target_lang=body.target_lang or "ja",
                max_words=body.max_words or 300,
            )
        else:
            logger.info(f"Processing {len(chunks)} chunks for long transcript")
            summary = gemini_summarize_multi(
                chunks,
                target_lang=body.target_lang or "ja",
                max_words=body.max_words or 300,
            )

        processing_time = time.time() - start_time
        logger.info(f"Successfully processed in {processing_time:.2f}s")

        return SummarizeResponse(
            url=body.url,
            title=body.title,
            channel=body.channel,
            original_lang=body.lang,
            target_lang=body.target_lang or "ja",
            transcript_length=len(body.transcript),
            chunks=len(chunks),
            summary=summary,
            processing_time=processing_time,
        )

    except Exception as e:
        logger.error(f"Summarization error: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")


@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "YouTube Transcript Hybrid Summarizer",
        "version": "1.0.0",
        "description": "Client-side transcript extraction + Server-side AI summarization",
        "endpoints": {
            "healthz": "GET /healthz - Health check",
            "summarize": "POST /summarize - Summarize transcript text",
        },
        "usage": "Use with Tampermonkey script or bookmarklet for seamless YouTube integration",
    }


if __name__ == "__main__":
    import uvicorn

    # Detect Cloud Run environment
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if is_cloud_run:
        # Cloud Run configuration
        host = "0.0.0.0"
        port = PORT
        log_level = "info"
    else:
        # Local development configuration
        host = "127.0.0.1"
        port = 8081  # Different from Flask version to avoid conflicts
        log_level = "debug"

    logger.info(f"Starting server on {host}:{port} (Cloud Run: {is_cloud_run})")

    uvicorn.run(
        "app_hybrid:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=not is_cloud_run,
    )
