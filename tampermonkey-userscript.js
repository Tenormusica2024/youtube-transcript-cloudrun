// ==UserScript==
// @name         YouTube Transcript Extractor - Easy Install
// @namespace    https://youtube-transcript.io/
// @version      1.0.0
// @description  YouTube動画プレイヤーに字幕抽出ボタンを追加（簡単インストール版）
// @author       YouTube Transcript Extractor Team
// @match        https://www.youtube.com/watch*
// @match        https://www.youtube.com/shorts/*
// @match        https://m.youtube.com/watch*
// @match        https://m.youtube.com/shorts/*
// @grant        GM_setValue
// @grant        GM_getValue
// @grant        GM_openInTab
// @grant        GM_registerMenuCommand
// @run-at       document-end
// @updateURL    https://raw.githubusercontent.com/Tenormusica2024/youtube-transcript-cloudrun/master/tampermonkey-userscript.js
// @downloadURL  https://raw.githubusercontent.com/Tenormusica2024/youtube-transcript-cloudrun/master/tampermonkey-userscript.js
// ==/UserScript==

(function() {
    'use strict';
    
    console.log('🚀 YouTube Transcript Extractor ユーザースクリプト開始');
    
    // 設定
    const CONFIG = {
        DEFAULT_SERVER_URL: 'http://localhost:8085',
        BUTTON_RETRY_INTERVAL: 1000,
        MAX_RETRY_COUNT: 10,
        OBSERVER_THROTTLE: 500
    };
    
    // サーバーURL設定管理
    const ServerConfig = {
        get: () => GM_getValue('serverUrl', CONFIG.DEFAULT_SERVER_URL),
        set: (url) => GM_setValue('serverUrl', url),
        
        // サーバーURL設定ダイアログ
        prompt: () => {
            const currentUrl = ServerConfig.get();
            const newUrl = prompt(
                'YouTube字幕抽出サーバーのURLを設定してください\n\n推奨設定:\n• ローカル: http://localhost:8085\n• ngrok: https://xxx.ngrok-free.app\n• 本番: https://your-domain.com',
                currentUrl
            );
            
            if (newUrl && newUrl.trim() !== currentUrl) {
                ServerConfig.set(newUrl.trim());
                alert('サーバーURL設定を保存しました: ' + newUrl.trim());
                return true;
            }
            return false;
        }
    };
    
    // Tampermonkey メニューコマンド登録
    GM_registerMenuCommand('⚙️ サーバーURL設定', ServerConfig.prompt);
    GM_registerMenuCommand('🔧 字幕抽出ツールを開く', () => {
        GM_openInTab(ServerConfig.get(), { active: true });
    });
    
    // YouTube動画ID抽出
    function extractVideoId(url = window.location.href) {
        try {
            const urlObj = new URL(url);
            
            // 通常動画: /watch?v=VIDEO_ID
            if (urlObj.pathname === '/watch') {
                return urlObj.searchParams.get('v');
            }
            
            // YouTube Shorts: /shorts/VIDEO_ID
            if (urlObj.pathname.startsWith('/shorts/')) {
                const match = urlObj.pathname.match(/\/shorts\/([^\/\?]+)/);
                return match ? match[1] : null;
            }
            
            // 短縮URL: youtu.be/VIDEO_ID
            if (urlObj.hostname === 'youtu.be') {
                return urlObj.pathname.slice(1).split('?')[0];
            }
            
            return null;
        } catch (error) {
            console.error('動画ID抽出エラー:', error);
            return null;
        }
    }
    
    // 字幕抽出ボタン作成
    function createTranscriptButton() {
        const button = document.createElement('button');
        button.id = 'yte-userscript-btn';
        button.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 4H4C2.9 4 2 4.9 2 6v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM4 18V6h16v12H4z"/>
                <path d="M6 10h2v2H6zm0 4h8v2H6zm10-4h2v2h-2z"/>
            </svg>
            <span>字幕抽出</span>
        `;
        
        // ボタンスタイル
        button.style.cssText = `
            display: flex !important;
            align-items: center !important;
            gap: 6px !important;
            padding: 8px 12px !important;
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 18px !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
            z-index: 9999 !important;
            position: relative !important;
            white-space: nowrap !important;
            font-family: 'Roboto', 'Arial', sans-serif !important;
        `;
        
        // ホバー効果
        button.addEventListener('mouseenter', () => {
            button.style.background = 'linear-gradient(135deg, #cc0000 0%, #990000 100%) !important';
            button.style.transform = 'translateY(-1px) !important';
            button.style.boxShadow = '0 4px 12px rgba(255, 0, 0, 0.3) !important';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.background = 'linear-gradient(135deg, #ff0000 0%, #cc0000 100%) !important';
            button.style.transform = 'translateY(0) !important';
            button.style.boxShadow = 'none !important';
        });
        
        // クリックイベント
        button.addEventListener('click', handleTranscriptExtraction);
        
        return button;
    }
    
    // 字幕抽出処理
    async function handleTranscriptExtraction() {
        const videoId = extractVideoId();
        if (!videoId) {
            alert('YouTube動画IDを取得できませんでした');
            return;
        }
        
        const serverUrl = ServerConfig.get();
        const currentUrl = window.location.href;
        const extractUrl = `${serverUrl}?url=${encodeURIComponent(currentUrl)}&auto_extract=true`;
        
        console.log('字幕抽出開始:', videoId, extractUrl);
        
        // 新しいタブで字幕抽出ツールを開く
        GM_openInTab(extractUrl, { active: true });
    }
    
    // ボタン挿入戦略
    class ButtonInserter {
        constructor() {
            this.retryCount = 0;
            this.currentButton = null;
            this.lastUrl = '';
        }
        
        // メイン挿入ロジック
        insertButton() {
            // URL変更チェック
            if (window.location.href !== this.lastUrl) {
                this.removeExistingButton();
                this.lastUrl = window.location.href;
                this.retryCount = 0;
            }
            
            // 既存ボタンチェック
            if (this.currentButton && document.contains(this.currentButton)) {
                return true;
            }
            
            // 挿入戦略実行
            const strategies = [
                () => this.insertIntoControlsRight(),
                () => this.insertIntoTopLevelButtons(),
                () => this.insertIntoPlayerActions(),
                () => this.insertBelowPlayer()
            ];
            
            for (const strategy of strategies) {
                if (strategy()) {
                    console.log('✅ YouTube字幕抽出ボタン挿入成功');
                    return true;
                }
            }
            
            return false;
        }
        
        // 戦略1: プレイヤーコントロール右側
        insertIntoControlsRight() {
            const controls = document.querySelector('.ytp-chrome-controls .ytp-right-controls');
            if (!controls) return false;
            
            const button = createTranscriptButton();
            button.style.cssText += `
                height: 32px !important;
                padding: 6px 10px !important;
                font-size: 12px !important;
                margin-left: 8px !important;
            `;
            
            controls.insertBefore(button, controls.firstChild);
            this.currentButton = button;
            return true;
        }
        
        // 戦略2: 動画タイトル下のボタンエリア
        insertIntoTopLevelButtons() {
            const container = document.querySelector('#top-level-buttons-computed');
            if (!container) return false;
            
            const button = createTranscriptButton();
            button.style.cssText += 'margin-right: 8px !important;';
            
            container.appendChild(button);
            this.currentButton = button;
            return true;
        }
        
        // 戦略3: プレイヤーアクション（いいね・共有エリア）
        insertIntoPlayerActions() {
            const actions = document.querySelector('#actions-inner');
            if (!actions) return false;
            
            const button = createTranscriptButton();
            button.style.cssText += 'margin-left: 8px !important;';
            
            actions.appendChild(button);
            this.currentButton = button;
            return true;
        }
        
        // 戦略4: プレイヤー下部（フォールバック）
        insertBelowPlayer() {
            const player = document.querySelector('#movie_player');
            if (!player) return false;
            
            const container = document.createElement('div');
            container.style.cssText = `
                padding: 10px 0 !important;
                text-align: right !important;
                border-bottom: 1px solid #e0e0e0 !important;
                margin-bottom: 12px !important;
            `;
            
            const button = createTranscriptButton();
            container.appendChild(button);
            
            const insertPoint = document.querySelector('#below-the-fold') || 
                               document.querySelector('#secondary-inner') || 
                               player.parentNode;
            
            if (insertPoint) {
                insertPoint.insertBefore(container, insertPoint.firstChild);
                this.currentButton = button;
                return true;
            }
            
            return false;
        }
        
        // 既存ボタン削除
        removeExistingButton() {
            const existing = document.querySelectorAll('#yte-userscript-btn');
            existing.forEach(btn => btn.remove());
            this.currentButton = null;
        }
        
        // リトライ機能付き挿入
        retryInsertion() {
            if (this.retryCount >= CONFIG.MAX_RETRY_COUNT) {
                console.warn('⚠️ YouTube字幕抽出ボタン挿入: 最大リトライ回数に到達');
                return;
            }
            
            if (!this.insertButton()) {
                this.retryCount++;
                setTimeout(() => this.retryInsertion(), CONFIG.BUTTON_RETRY_INTERVAL);
            }
        }
    }
    
    // DOM変更監視
    class YouTubeObserver {
        constructor() {
            this.inserter = new ButtonInserter();
            this.throttleTimer = null;
        }
        
        start() {
            // 初回挿入試行
            this.inserter.retryInsertion();
            
            // YouTube SPA対応
            this.observeDocumentChanges();
            this.observeYouTubeEvents();
            
            console.log('🔍 YouTube DOM監視開始');
        }
        
        observeDocumentChanges() {
            const observer = new MutationObserver(() => {
                this.throttledButtonInsertion();
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        observeYouTubeEvents() {
            // YouTube SPA ナビゲーション
            window.addEventListener('yt-navigate-finish', () => {
                setTimeout(() => this.inserter.retryInsertion(), 500);
            });
            
            // popstate（ブラウザバック/フォワード）
            window.addEventListener('popstate', () => {
                setTimeout(() => this.inserter.retryInsertion(), 500);
            });
        }
        
        throttledButtonInsertion() {
            if (this.throttleTimer) return;
            
            this.throttleTimer = setTimeout(() => {
                this.inserter.insertButton();
                this.throttleTimer = null;
            }, CONFIG.OBSERVER_THROTTLE);
        }
    }
    
    // 初期化
    function initialize() {
        // YouTube動画ページ判定
        if (!window.location.href.includes('youtube.com/watch') && 
            !window.location.href.includes('youtube.com/shorts/')) {
            return;
        }
        
        console.log('🎬 YouTube動画ページを検出');
        
        // DOM読み込み待機
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(startObserver, 1000);
            });
        } else {
            setTimeout(startObserver, 1000);
        }
    }
    
    function startObserver() {
        const observer = new YouTubeObserver();
        observer.start();
    }
    
    // スクリプト開始
    initialize();
    
})();