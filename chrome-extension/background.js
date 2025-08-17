/**
 * YouTube Transcript Extractor - Background Script
 * Service Worker for Chrome Extension
 */

// インストール・更新時の処理
chrome.runtime.onInstalled.addListener((details) => {
    console.log('🚀 YouTube Transcript Extractor インストール完了');
    
    if (details.reason === 'install') {
        // 初回インストール時
        chrome.storage.sync.set({
            serverUrl: 'http://localhost:8085',
            autoExtract: false,
            defaultLanguage: 'ja'
        });
        
        // ようこそページを開く
        chrome.tabs.create({
            url: chrome.runtime.getURL('web_transcript_interface.html')
        });
    } else if (details.reason === 'update') {
        // 更新時
        console.log('拡張機能が更新されました');
    }
});

// 拡張機能アイコンクリック時の処理
chrome.action.onClicked.addListener(async (tab) => {
    console.log('拡張機能アイコンがクリックされました:', tab.url);
    
    // YouTube動画ページの場合は直接処理
    if (isYouTubeVideoPage(tab.url)) {
        await handleYouTubeVideoExtraction(tab);
    } else {
        // それ以外の場合はポップアップを表示（manifest.jsonのactionで自動処理）
        console.log('YouTube以外のページです');
    }
});

// コンテキストメニューの設定
chrome.runtime.onInstalled.addListener(() => {
    // YouTube動画ページ用のコンテキストメニュー
    chrome.contextMenus.create({
        id: 'extract-transcript',
        title: '字幕を抽出・要約',
        contexts: ['page'],
        documentUrlPatterns: [
            'https://www.youtube.com/watch*',
            'https://www.youtube.com/shorts/*',
            'https://m.youtube.com/watch*',
            'https://m.youtube.com/shorts/*'
        ]
    });
    
    // リンク用のコンテキストメニュー
    chrome.contextMenus.create({
        id: 'extract-transcript-link',
        title: 'このYouTube動画の字幕を抽出',
        contexts: ['link'],
        targetUrlPatterns: [
            'https://www.youtube.com/watch*',
            'https://www.youtube.com/shorts/*',
            'https://youtu.be/*'
        ]
    });
});

// コンテキストメニュークリック時の処理
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    console.log('コンテキストメニューがクリックされました:', info.menuItemId);
    
    if (info.menuItemId === 'extract-transcript') {
        await handleYouTubeVideoExtraction(tab);
    } else if (info.menuItemId === 'extract-transcript-link') {
        await handleYouTubeVideoExtraction(tab, info.linkUrl);
    }
});

// メッセージハンドリング
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('バックグラウンドでメッセージを受信:', request);
    
    if (request.action === 'extractTranscript') {
        handleTranscriptExtraction(request.url, request.options)
            .then(result => sendResponse({ success: true, data: result }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true; // 非同期レスポンス
    } else if (request.action === 'getServerStatus') {
        getServerStatus()
            .then(status => sendResponse({ success: true, status }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    } else if (request.action === 'openTranscriptTool') {
        openTranscriptTool(request.url)
            .then(() => sendResponse({ success: true }))
            .catch(error => sendResponse({ success: false, error: error.message }));
        return true;
    }
});

// YouTube動画ページかどうかを判定
function isYouTubeVideoPage(url) {
    if (!url) return false;
    return (url.includes('youtube.com/watch') || 
            url.includes('youtube.com/shorts/') ||
            url.includes('m.youtube.com/watch') ||
            url.includes('m.youtube.com/shorts/') ||
            url.includes('youtu.be/'));
}

// YouTube動画IDを抽出
function extractVideoId(url) {
    try {
        const urlObj = new URL(url);
        
        // 通常動画
        if (urlObj.pathname === '/watch') {
            return urlObj.searchParams.get('v');
        }
        
        // YouTube Shorts
        if (urlObj.pathname.startsWith('/shorts/')) {
            const match = urlObj.pathname.match(/\/shorts\/([^\/\?]+)/);
            return match ? match[1] : null;
        }
        
        // 短縮URL
        if (urlObj.hostname === 'youtu.be') {
            return urlObj.pathname.slice(1).split('?')[0];
        }
        
        return null;
    } catch (error) {
        console.error('動画ID抽出エラー:', error);
        return null;
    }
}

// YouTube動画の字幕抽出処理
async function handleYouTubeVideoExtraction(tab, customUrl = null) {
    try {
        const targetUrl = customUrl || tab.url;
        const videoId = extractVideoId(targetUrl);
        
        if (!videoId) {
            throw new Error('動画IDを取得できませんでした');
        }
        
        console.log('字幕抽出開始:', videoId);
        
        // 設定を取得
        const settings = await chrome.storage.sync.get([
            'serverUrl', 
            'autoExtract', 
            'defaultLanguage'
        ]);
        
        const serverUrl = settings.serverUrl || 'http://localhost:8085';
        
        // 字幕抽出ツールを開く
        const extractUrl = `${serverUrl}?url=${encodeURIComponent(targetUrl)}&auto_extract=true`;
        
        await chrome.tabs.create({
            url: extractUrl,
            active: true
        });
        
        // 通知を表示
        await chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon-48.png',
            title: 'YouTube字幕抽出',
            message: '字幕抽出ツールを起動しました'
        });
        
    } catch (error) {
        console.error('字幕抽出処理エラー:', error);
        
        // エラー通知
        await chrome.notifications.create({
            type: 'basic',
            iconUrl: 'icons/icon-48.png',
            title: 'YouTube字幕抽出エラー',
            message: error.message
        });
    }
}

// 字幕抽出API呼び出し
async function handleTranscriptExtraction(url, options = {}) {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:8085';
    
    const response = await fetch(`${serverUrl}/api/extract`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: url,
            language: options.language || 'ja',
            format: options.format !== false
        })
    });
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.error || '字幕抽出に失敗しました');
    }
    
    return result.data;
}

// サーバー状態確認
async function getServerStatus() {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:8085';
    
    try {
        const response = await fetch(`${serverUrl}/health`, {
            method: 'GET',
            timeout: 5000
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        return {
            connected: true,
            version: data.version,
            services: data.services
        };
    } catch (error) {
        return {
            connected: false,
            error: error.message
        };
    }
}

// 字幕抽出ツールを開く
async function openTranscriptTool(url = null) {
    const settings = await chrome.storage.sync.get(['serverUrl']);
    const serverUrl = settings.serverUrl || 'http://localhost:8085';
    
    const toolUrl = url ? 
        `${serverUrl}?url=${encodeURIComponent(url)}` : 
        serverUrl;
    
    await chrome.tabs.create({
        url: toolUrl,
        active: true
    });
}

// 拡張機能の無効化・削除時の処理
chrome.runtime.onSuspend.addListener(() => {
    console.log('YouTube Transcript Extractor サスペンド');
});

// エラーハンドリング
chrome.runtime.onStartup.addListener(() => {
    console.log('YouTube Transcript Extractor 起動');
});

// 設定変更の監視
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (namespace === 'sync') {
        console.log('設定が変更されました:', changes);
        
        // サーバーURL変更時の処理
        if (changes.serverUrl) {
            console.log('サーバーURL更新:', changes.serverUrl.newValue);
        }
    }
});

// タブ更新の監視（YouTube SPA対応）
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // ページ読み込み完了時かつYouTube動画ページの場合
    if (changeInfo.status === 'complete' && isYouTubeVideoPage(tab.url)) {
        // コンテンツスクリプトにページ変更を通知
        try {
            await chrome.tabs.sendMessage(tabId, {
                action: 'pageChanged',
                url: tab.url
            });
        } catch (error) {
            // コンテンツスクリプトが読み込まれていない場合は無視
            console.log('コンテンツスクリプト通信エラー（正常）:', error.message);
        }
    }
});

// 通知クリック時の処理
chrome.notifications.onClicked.addListener((notificationId) => {
    console.log('通知がクリックされました:', notificationId);
    chrome.notifications.clear(notificationId);
});

console.log('🔧 YouTube Transcript Extractor バックグラウンドスクリプト初期化完了');