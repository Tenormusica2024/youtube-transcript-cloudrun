// ==UserScript==
// @name         YouTube Transcript → Cloud Run Hybrid Summarizer
// @namespace    https://github.com/tenormusica/yt-summarizer
// @version      1.0.0
// @description  Extract YouTube transcripts on client-side and summarize via Cloud Run
// @match        https://www.youtube.com/watch*
// @match        https://m.youtube.com/watch*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @grant        GM_setValue
// @grant        GM_getValue
// @run-at       document-idle
// @updateURL    https://raw.githubusercontent.com/tenormusica/yt-summarizer/main/tampermonkey_script.js
// @downloadURL  https://raw.githubusercontent.com/tenormusica/yt-summarizer/main/tampermonkey_script.js
// ==/UserScript==

(function() {
    "use strict";

    // ==== Configuration ====
    // Cloud Run deployment URL
    const API_ENDPOINT = GM_getValue("API_ENDPOINT") || "https://yt-transcript-hybrid-2yy4vkcmia-uc.a.run.app/summarize";
    const API_TOKEN = GM_getValue("API_TOKEN") || "hybrid-yt-token-2024";
    const TARGET_LANG = GM_getValue("TARGET_LANG") || "ja";
    const MAX_WORDS = parseInt(GM_getValue("MAX_WORDS")) || 300;
    
    // Debug mode
    const DEBUG_MODE = GM_getValue("DEBUG_MODE") || false;

    // ==== UI Styling ====
    GM_addStyle(`
        #ytSummarizeBtn {
            position: fixed;
            right: 20px;
            top: 20px;
            z-index: 999999;
            padding: 15px 20px;
            background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
            color: white;
            border: 3px solid white;
            border-radius: 8px;
            font-weight: 700;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 0 8px 20px rgba(0,0,0,0.5);
            transition: all 0.3s ease;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            min-width: 120px;
            text-align: center;
        }
        
        #ytSummarizeBtn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.4);
        }
        
        #ytSummarizeBtn[disabled] {
            opacity: 0.6;
            cursor: wait;
            transform: none;
        }
        
        .yt-summary-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .yt-summary-content {
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .yt-summary-close {
            position: absolute;
            top: 12px;
            right: 16px;
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        
        .yt-summary-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #333;
        }
        
        .yt-summary-meta {
            background: #f5f5f5;
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 16px;
            font-size: 14px;
            color: #666;
        }
        
        .yt-summary-text {
            line-height: 1.6;
            color: #333;
            white-space: pre-wrap;
        }
        
        .yt-summary-actions {
            margin-top: 20px;
            text-align: center;
        }
        
        .yt-summary-btn {
            background: #4ECDC4;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            margin: 0 8px;
            font-weight: 500;
        }
        
        .yt-summary-btn:hover {
            background: #45B7AF;
        }
    `);

    // ==== Utility Functions ====
    function log(...args) {
        if (DEBUG_MODE) {
            console.log("[YT-Summarizer]", ...args);
        }
    }
    
    function logError(...args) {
        console.error("[YT-Summarizer ERROR]", ...args);
    }

    // ==== UI Management ====
    function ensureButton() {
        if (document.getElementById("ytSummarizeBtn")) return;
        
        const btn = document.createElement("button");
        btn.id = "ytSummarizeBtn";
        btn.textContent = "🤖 AI要約";
        btn.title = "YouTube動画をAIで要約 (Cloud Run)";
        btn.addEventListener("click", startSummarizationFlow);
        document.body.appendChild(btn);
        
        log("Summarize button added");
    }

    function updateButtonState(text, disabled = false) {
        const btn = document.getElementById("ytSummarizeBtn");
        if (btn) {
            btn.textContent = text;
            btn.disabled = disabled;
        }
    }

    function showModal(title, content, meta = null) {
        const modal = document.createElement("div");
        modal.className = "yt-summary-modal";
        
        const modalContent = document.createElement("div");
        modalContent.className = "yt-summary-content";
        
        modalContent.innerHTML = `
            <button class="yt-summary-close">×</button>
            <div class="yt-summary-title">${title}</div>
            ${meta ? `<div class="yt-summary-meta">${meta}</div>` : ''}
            <div class="yt-summary-text">${content}</div>
            <div class="yt-summary-actions">
                <button class="yt-summary-btn" onclick="navigator.clipboard.writeText(this.parentElement.previousElementSibling.textContent).then(() => alert('クリップボードにコピーしました！'))">📋 コピー</button>
                <button class="yt-summary-btn" onclick="this.closest('.yt-summary-modal').remove()">閉じる</button>
            </div>
        `;
        
        modalContent.querySelector(".yt-summary-close").addEventListener("click", () => {
            modal.remove();
        });
        
        modal.addEventListener("click", (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
    }

    // ==== YouTube Transcript Extraction ====
    function getInitialPlayerResponse() {
        // Try direct access first
        if (window.ytInitialPlayerResponse) {
            log("Found ytInitialPlayerResponse in window object");
            return window.ytInitialPlayerResponse;
        }

        // Fallback: Parse from script tags
        const scripts = document.querySelectorAll("script");
        for (const script of scripts) {
            const text = script.textContent || "";
            if (text.includes("ytInitialPlayerResponse")) {
                const match = text.match(/ytInitialPlayerResponse\s*=\s*(\{.+?\});/s);
                if (match) {
                    try {
                        const response = JSON.parse(match[1]);
                        log("Parsed ytInitialPlayerResponse from script tag");
                        return response;
                    } catch (e) {
                        log("Failed to parse ytInitialPlayerResponse:", e);
                    }
                }
            }
        }
        
        return null;
    }

    async function fetchTranscriptFromUrl(baseUrl) {
        try {
            const url = baseUrl.includes("fmt=") ? baseUrl : baseUrl + "&fmt=json3";
            log("Fetching transcript from:", url);
            
            const response = await fetch(url, {
                credentials: "include",
                headers: {
                    "User-Agent": navigator.userAgent,
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            log("Raw transcript data:", data);
            
            // Parse JSON3 format
            const lines = [];
            if (data && Array.isArray(data.events)) {
                for (const event of data.events) {
                    if (event.segs) {
                        const lineText = event.segs.map(seg => seg.utf8 || "").join("");
                        if (lineText.trim()) {
                            lines.push(lineText.trim());
                        }
                    }
                }
            }
            
            const transcript = lines
                .join("\n")
                .replace(/\s*\n\s*/g, "\n")
                .replace(/\n{3,}/g, "\n\n")
                .trim();
            
            log("Extracted transcript length:", transcript.length);
            return transcript;
            
        } catch (error) {
            logError("Failed to fetch transcript:", error);
            throw new Error(`字幕取得エラー: ${error.message}`);
        }
    }

    async function getTranscriptData() {
        const playerResponse = getInitialPlayerResponse();
        if (!playerResponse) {
            throw new Error("YouTube player data not found. Please refresh the page.");
        }

        const captions = playerResponse.captions;
        if (!captions || !captions.playerCaptionsTracklistRenderer) {
            throw new Error("この動画には字幕がありません（ライブ配信、限定公開、字幕無効化など）");
        }

        const tracks = captions.playerCaptionsTracklistRenderer.captionTracks || [];
        if (tracks.length === 0) {
            throw new Error("利用可能な字幕トラックがありません");
        }

        log("Available tracks:", tracks.map(t => `${t.languageCode} (${t.name?.simpleText || 'No name'})`));

        // Language priority: user preference > Japanese > English > first available
        const userLang = navigator.language?.slice(0, 2) || "en";
        const selectedTrack = tracks.find(t => t.languageCode === TARGET_LANG) ||
                             tracks.find(t => t.languageCode === userLang) ||
                             tracks.find(t => t.languageCode.startsWith("ja")) ||
                             tracks.find(t => t.languageCode.startsWith("en")) ||
                             tracks[0];

        log("Selected track:", selectedTrack.languageCode, selectedTrack.name?.simpleText);

        const transcript = await fetchTranscriptFromUrl(selectedTrack.baseUrl);
        if (!transcript || transcript.length < 10) {
            throw new Error("字幕の内容が取得できませんでした（空の字幕またはアクセス拒否）");
        }

        return {
            text: transcript,
            language: selectedTrack.languageCode,
            trackName: selectedTrack.name?.simpleText || "Unknown"
        };
    }

    // ==== Video Information Extraction ====
    function extractVideoInfo() {
        const url = window.location.href;
        const title = document.title.replace(" - YouTube", "").trim();
        
        // Try multiple selectors for channel name
        const channelSelectors = [
            "#text-container.ytd-channel-name #text",
            "ytd-channel-name a",
            ".ytd-channel-name a",
            "[id='channel-name'] a",
            ".ytd-video-owner-renderer a"
        ];
        
        let channel = null;
        for (const selector of channelSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent?.trim()) {
                channel = element.textContent.trim();
                break;
            }
        }
        
        return { url, title, channel };
    }

    // ==== Cloud Run API Communication ====
    async function sendToCloudRun(payload) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: "POST",
                url: API_ENDPOINT,
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${API_TOKEN}`,
                },
                data: JSON.stringify(payload),
                timeout: 60000, // 60 seconds
                onload: function(response) {
                    log("API Response:", response.status, response.statusText);
                    if (response.status >= 200 && response.status < 300) {
                        try {
                            const data = JSON.parse(response.responseText);
                            resolve(data);
                        } catch (e) {
                            reject(new Error(`Invalid JSON response: ${e.message}`));
                        }
                    } else {
                        reject(new Error(`API Error ${response.status}: ${response.responseText}`));
                    }
                },
                onerror: function(error) {
                    logError("Network error:", error);
                    reject(new Error("Network error: Unable to reach the summarization service"));
                },
                ontimeout: function() {
                    reject(new Error("Request timeout: The summarization service took too long to respond"));
                }
            });
        });
    }

    // ==== Main Summarization Flow ====
    async function startSummarizationFlow() {
        updateButtonState("🔄 処理中...", true);
        
        try {
            // Step 1: Extract video information
            const videoInfo = extractVideoInfo();
            log("Video info:", videoInfo);
            
            // Step 2: Extract transcript
            updateButtonState("📝 字幕取得中...", true);
            const transcriptData = await getTranscriptData();
            log("Transcript data:", {
                length: transcriptData.text.length,
                language: transcriptData.language
            });
            
            // Step 3: Prepare API payload
            const payload = {
                url: videoInfo.url,
                title: videoInfo.title,
                channel: videoInfo.channel,
                transcript: transcriptData.text,
                lang: transcriptData.language,
                target_lang: TARGET_LANG,
                max_words: MAX_WORDS
            };
            
            // Step 4: Send to Cloud Run for summarization
            updateButtonState("🤖 AI要約中...", true);
            const result = await sendToCloudRun(payload);
            log("Summarization result:", result);
            
            // Step 5: Display results
            const meta = `
                <strong>動画:</strong> ${result.title || "Unknown"}<br>
                <strong>チャンネル:</strong> ${result.channel || "Unknown"}<br>
                <strong>字幕言語:</strong> ${result.original_lang || "Unknown"}<br>
                <strong>文字数:</strong> ${result.transcript_length?.toLocaleString() || "Unknown"}文字<br>
                <strong>処理時間:</strong> ${result.processing_time?.toFixed(1) || "Unknown"}秒<br>
                <strong>チャンク数:</strong> ${result.chunks || "Unknown"}
            `;
            
            showModal("🤖 AI要約結果", result.summary, meta);
            
            // Copy to clipboard automatically
            try {
                await navigator.clipboard.writeText(result.summary);
                log("Summary copied to clipboard");
            } catch (e) {
                log("Failed to copy to clipboard:", e);
            }
            
        } catch (error) {
            logError("Summarization failed:", error);
            showModal(
                "❌ エラー", 
                `要約処理でエラーが発生しました:\n\n${error.message}\n\n考えられる原因:\n- この動画には字幕がありません\n- サーバーが一時的に利用できません\n- ネットワーク接続に問題があります`
            );
        } finally {
            updateButtonState("🤖 AI要約", false);
        }
    }

    // ==== Settings Management ====
    function showSettings() {
        const currentEndpoint = GM_getValue("API_ENDPOINT") || API_ENDPOINT;
        const currentToken = GM_getValue("API_TOKEN") || API_TOKEN;
        const currentLang = GM_getValue("TARGET_LANG") || TARGET_LANG;
        const currentWords = GM_getValue("MAX_WORDS") || MAX_WORDS;
        const currentDebug = GM_getValue("DEBUG_MODE") || false;
        
        const settingsModal = `
            <h3>設定</h3>
            <p><strong>API Endpoint:</strong><br>
            <input type="text" id="settingsEndpoint" style="width:100%; padding:8px; margin:4px 0;" value="${currentEndpoint}"></p>
            
            <p><strong>API Token:</strong><br>
            <input type="password" id="settingsToken" style="width:100%; padding:8px; margin:4px 0;" value="${currentToken}"></p>
            
            <p><strong>要約言語:</strong><br>
            <select id="settingsLang" style="width:100%; padding:8px; margin:4px 0;">
                <option value="ja" ${currentLang === 'ja' ? 'selected' : ''}>日本語</option>
                <option value="en" ${currentLang === 'en' ? 'selected' : ''}>English</option>
            </select></p>
            
            <p><strong>目標語数:</strong><br>
            <input type="number" id="settingsWords" style="width:100%; padding:8px; margin:4px 0;" value="${currentWords}" min="100" max="1000" step="50"></p>
            
            <p><label>
                <input type="checkbox" id="settingsDebug" ${currentDebug ? 'checked' : ''}> デバッグモード
            </label></p>
            
            <div style="text-align: center; margin-top: 20px;">
                <button onclick="saveSettings()" style="background:#4ECDC4; color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer; margin-right:10px;">保存</button>
                <button onclick="this.closest('.yt-summary-modal').remove()" style="background:#666; color:white; border:none; padding:10px 20px; border-radius:6px; cursor:pointer;">キャンセル</button>
            </div>
        `;
        
        showModal("⚙️ YouTube AI要約 設定", settingsModal);
        
        // Add save function to global scope temporarily
        window.saveSettings = function() {
            GM_setValue("API_ENDPOINT", document.getElementById("settingsEndpoint").value);
            GM_setValue("API_TOKEN", document.getElementById("settingsToken").value);
            GM_setValue("TARGET_LANG", document.getElementById("settingsLang").value);
            GM_setValue("MAX_WORDS", parseInt(document.getElementById("settingsWords").value));
            GM_setValue("DEBUG_MODE", document.getElementById("settingsDebug").checked);
            
            alert("設定を保存しました。ページをリロードして反映してください。");
            document.querySelector(".yt-summary-modal").remove();
            delete window.saveSettings;
        };
    }

    // ==== Keyboard Shortcuts ====
    document.addEventListener("keydown", function(e) {
        // Ctrl+Shift+S: Start summarization
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            startSummarizationFlow();
        }
        
        // Ctrl+Shift+C: Open settings
        if (e.ctrlKey && e.shiftKey && e.key === 'C') {
            e.preventDefault();
            showSettings();
        }
    });

    // ==== Initialization ====
    function initialize() {
        log("Initializing YouTube AI Summarizer");
        ensureButton();
        
        // Monitor for YouTube page changes
        const observer = new MutationObserver(() => {
            ensureButton();
        });
        
        observer.observe(document.documentElement, {
            childList: true,
            subtree: true
        });
        
        log("Initialization complete");
    }

    // Start the extension
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initialize);
    } else {
        initialize();
    }

})();