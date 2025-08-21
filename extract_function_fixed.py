def extract_youtube_transcript(video_url, language_code="ja"):
    """YouTube字幕抽出（Shorts対応＆堅牢フォールバック）"""
    try:
        # --- 動画ID抽出 ---
        parsed_url = urlparse(video_url)
        video_id = None
        if "youtube.com" in parsed_url.netloc or "m.youtube.com" in parsed_url.netloc:
            if parsed_url.path == "/watch":
                video_id = parse_qs(parsed_url.query).get("v", [None])[0]
            elif parsed_url.path.startswith("/shorts/"):
                video_id = parsed_url.path.split("/shorts/")[1].split("?")[0]
            elif parsed_url.path.startswith("/embed/"):
                video_id = parsed_url.path.split("/embed/")[1].split("?")[0]
            elif parsed_url.path.startswith("/v/"):
                video_id = parsed_url.path.split("/v/")[1].split("?")[0]
        elif "youtu.be" in parsed_url.netloc:
            video_id = parsed_url.path.lstrip("/").split("?")[0]

        if not video_id:
            raise ValueError("有効なYouTube URLではありません")

        video_id = video_id.split("&")[0]
        logger.info(f"[extract] video_id={video_id}")

        # --- 言語フォールバック順 ---
        langs = []
        if language_code and language_code != "auto":
            langs.append(language_code)
        for l in ["ja", "en"]:
            if l not in langs:
                langs.append(l)

        # --- 正式API: get_transcript を優先 ---
        for l in langs:
            try:
                data = YouTubeTranscriptApi.get_transcript(video_id, languages=[l])
                full_text = " ".join([item["text"] for item in data])
                return {
                    "success": True,
                    "transcript": full_text,
                    "language": l,
                    "video_id": video_id,
                }
            except NoTranscriptFound:
                continue
            except TranscriptsDisabled:
                raise ValueError("この動画の字幕は無効化されています")

        # --- まだダメなら list_transcripts で取得可能なものを拾う ---
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
            preferred = [
                t
                for t in transcripts
                if getattr(t, "language_code", None) in ("ja", "en")
            ]
            ordered = preferred + [t for t in transcripts if t not in preferred]
            for t in ordered:
                try:
                    data = t.fetch()
                    full_text = " ".join([item["text"] for item in data])
                    return {
                        "success": True,
                        "transcript": full_text,
                        "language": getattr(t, "language_code", "unknown"),
                        "video_id": video_id,
                    }
                except Exception as inner_e:
                    logger.warning(f"[extract] fallback fetch failed: {inner_e}")
                    continue
        except Exception as list_e:
            logger.warning(f"[extract] list_transcripts failed: {list_e}")

        raise ValueError("利用可能な字幕が見つかりませんでした")

    except Exception as e:
        logger.error(f"[extract] error: {e}")
        return {"success": False, "error": str(e)}
