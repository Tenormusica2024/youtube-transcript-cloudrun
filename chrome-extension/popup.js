/**
 * YouTube Transcript Extractor - Popup Script
 * 拡張機能ポップアップの制御
 */

class ExtensionPopup {
    constructor() {
        this.serverUrl = 'http://localhost:8085';
        this.currentTab = null;
        this.currentVideoId = null;
        
        this.init();
    }
    
    async init() {
        console.log('🚀 拡張機能ポップアップ初期化');
        
        // DOM要素を取得
        this.elements = {
            pageStatus: document.getElementById('pageStatus'),
            videoId: document.getElementById('videoId'),
            serverStatus: document.getElementById('serverStatus'),
            extractBtn: document.getElementById('extractBtn'),
            extractText: document.getElementById('extractText'),
            openToolBtn: document.getElementById('openToolBtn'),
            serverUrl: document.getElementById('serverUrl'),
            testConnectionBtn: document.getElementById('testConnectionBtn'),
            notification: document.getElementById('notification')
        };
        
        // イベントリスナー設定
        this.setupEventListeners();
        
        // 設定を読み込み
        await this.loadSettings();
        
        // 現在のタブ情報を取得
        await this.getCurrentTab();
        
        // 初期チェック実行
        await this.checkCurrentPage();
        await this.testServerConnection();
    }
    
    setupEventListeners() {
        // 字幕抽出ボタン
        this.elements.extractBtn.addEventListener('click', () => {
            this.extractTranscript();
        });
        
        // ツールを開くボタン
        this.elements.openToolBtn.addEventListener('click', () => {
            this.openTranscriptTool();
        });
        
        // 接続テストボタン
        this.elements.testConnectionBtn.addEventListener('click', () => {
            this.testServerConnection(true);
        });
        
        // サーバーURL変更
        this.elements.serverUrl.addEventListener('change', () => {
            this.saveServerUrl();
        });
        
        this.elements.serverUrl.addEventListener('blur', () => {
            this.saveServerUrl();
        });
    }
    
    async loadSettings() {
        try {
            const result = await chrome.storage.sync.get(['serverUrl']);
            if (result.serverUrl) {
                this.serverUrl = result.serverUrl;
                this.elements.serverUrl.value = this.serverUrl;
            }
        } catch (error) {
            console.warn('設定読み込み失敗:', error);
        }
    }
    
    async saveServerUrl() {
        const newUrl = this.elements.serverUrl.value.trim();
        if (newUrl && newUrl !== this.serverUrl) {
            this.serverUrl = newUrl;
            try {
                await chrome.storage.sync.set({ serverUrl: this.serverUrl });
                console.log('サーバーURL保存:', this.serverUrl);
                this.showNotification('設定を保存しました', 'success');
            } catch (error) {
                console.error('設定保存失敗:', error);
                this.showNotification('設定の保存に失敗しました', 'error');
            }
        }
    }
    
    async getCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentTab = tab;
            return tab;
        } catch (error) {
            console.error('タブ情報取得失敗:', error);
            return null;
        }
    }
    
    async checkCurrentPage() {
        if (!this.currentTab) {
            this.updatePageStatus('タブ情報なし', 'error');
            return;
        }
        
        const url = this.currentTab.url;
        
        // YouTube動画ページかどうか確認
        if (this.isYouTubeVideoPage(url)) {
            this.currentVideoId = this.getVideoIdFromUrl(url);
            
            if (this.currentVideoId) {
                this.updatePageStatus('YouTube動画', 'ok');
                this.elements.videoId.textContent = this.currentVideoId;
                this.elements.videoId.className = 'status-value status-ok';
                this.elements.extractBtn.disabled = false;
            } else {
                this.updatePageStatus('YouTube (動画ID不明)', 'warning');
                this.elements.videoId.textContent = '取得失敗';
                this.elements.videoId.className = 'status-value status-error';
            }
        } else {
            this.updatePageStatus('YouTube以外', 'error');
            this.elements.videoId.textContent = '-';
            this.elements.videoId.className = 'status-value status-error';
        }
    }
    
    isYouTubeVideoPage(url) {
        if (!url) return false;
        return (url.includes('youtube.com/watch') || 
                url.includes('youtube.com/shorts/') ||
                url.includes('m.youtube.com/watch') ||
                url.includes('m.youtube.com/shorts/'));
    }
    
    getVideoIdFromUrl(url) {
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
            
            return null;
        } catch (error) {
            console.error('動画ID抽出エラー:', error);
            return null;
        }
    }
    
    updatePageStatus(text, status) {
        this.elements.pageStatus.textContent = text;
        this.elements.pageStatus.className = `status-value status-${status}`;
    }
    
    async testServerConnection(showNotification = false) {
        this.elements.serverStatus.innerHTML = '<span class="loading"></span>確認中...';
        this.elements.serverStatus.className = 'status-value';
        
        try {
            const response = await fetch(`${this.serverUrl}/health`, {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                this.elements.serverStatus.textContent = '接続OK';
                this.elements.serverStatus.className = 'status-value status-ok';
                
                if (showNotification) {
                    this.showNotification(`サーバー接続成功 (v${data.version || 'Unknown'})`, 'success');
                }
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('サーバー接続テスト失敗:', error);
            this.elements.serverStatus.textContent = '接続失敗';
            this.elements.serverStatus.className = 'status-value status-error';
            
            if (showNotification) {
                this.showNotification('サーバーに接続できません', 'error');
            }
        }
    }
    
    async extractTranscript() {
        if (!this.currentTab || !this.currentVideoId) {
            this.showNotification('YouTube動画ページで実行してください', 'error');
            return;
        }
        
        // ローディング状態
        this.elements.extractBtn.disabled = true;
        this.elements.extractText.innerHTML = '<span class="loading"></span>抽出中...';
        
        try {
            // 字幕抽出API呼び出し
            const response = await fetch(`${this.serverUrl}/api/extract`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: this.currentTab.url,
                    language: 'ja',
                    format: true
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('字幕抽出完了！', 'success');
                
                // 結果を新しいタブで表示
                const resultUrl = `${this.serverUrl}?result=${encodeURIComponent(JSON.stringify(result.data))}`;
                await chrome.tabs.create({ url: resultUrl });
                
                // ポップアップを閉じる
                setTimeout(() => window.close(), 1000);
            } else {
                throw new Error(result.error || '字幕抽出に失敗しました');
            }
        } catch (error) {
            console.error('字幕抽出エラー:', error);
            this.showNotification(`エラー: ${error.message}`, 'error');
        } finally {
            // ローディング解除
            this.elements.extractBtn.disabled = false;
            this.elements.extractText.textContent = '字幕抽出開始';
        }
    }
    
    async openTranscriptTool() {
        try {
            const url = this.currentTab ? 
                `${this.serverUrl}?url=${encodeURIComponent(this.currentTab.url)}` :
                this.serverUrl;
                
            await chrome.tabs.create({ url });
            window.close();
        } catch (error) {
            console.error('ツール起動エラー:', error);
            this.showNotification('ツールの起動に失敗しました', 'error');
        }
    }
    
    showNotification(message, type = 'success') {
        this.elements.notification.textContent = message;
        this.elements.notification.className = `notification notification-${type}`;
        this.elements.notification.style.display = 'block';
        
        // 自動消去
        setTimeout(() => {
            this.elements.notification.style.display = 'none';
        }, 3000);
    }
}

// ポップアップ初期化
document.addEventListener('DOMContentLoaded', () => {
    new ExtensionPopup();
});

// 共通ユーティリティ関数
window.ExtensionUtils = {
    // 設定値取得
    async getSetting(key, defaultValue = null) {
        try {
            const result = await chrome.storage.sync.get([key]);
            return result[key] !== undefined ? result[key] : defaultValue;
        } catch (error) {
            console.error('設定取得エラー:', error);
            return defaultValue;
        }
    },
    
    // 設定値保存
    async setSetting(key, value) {
        try {
            await chrome.storage.sync.set({ [key]: value });
            return true;
        } catch (error) {
            console.error('設定保存エラー:', error);
            return false;
        }
    },
    
    // YouTube動画ID抽出
    extractVideoId(url) {
        if (!url) return null;
        
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
};