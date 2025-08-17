/**
 * YouTube Transcript Extractor - Content Script
 * YouTube動画プレイヤー下部に字幕抽出ボタンを追加
 */

class YouTubeTranscriptExtractor {
    constructor() {
        this.serverUrl = 'http://localhost:8085';
        this.buttonAdded = false;
        this.currentVideoId = null;
        
        this.init();
    }
    
    init() {
        console.log('🚀 YouTube Transcript Extractor - 初期化開始');
        
        // サーバー設定を読み込み
        this.loadServerSettings();
        
        // YouTube DOM監視開始
        this.observeYouTubeChanges();
        
        // 初回実行
        this.checkAndAddButton();
        
        // URLハッシュ変更の監視（YouTube SPA対応）
        window.addEventListener('yt-navigate-finish', () => {
            setTimeout(() => this.checkAndAddButton(), 1000);
        });
        
        // popstate監視（戻る・進むボタン対応）
        window.addEventListener('popstate', () => {
            setTimeout(() => this.checkAndAddButton(), 1000);
        });
    }
    
    async loadServerSettings() {
        try {
            const result = await chrome.storage.sync.get(['serverUrl']);
            if (result.serverUrl) {
                this.serverUrl = result.serverUrl;
            }
            console.log(`📡 サーバーURL設定: ${this.serverUrl}`);
        } catch (error) {
            console.warn('⚠️ サーバー設定読み込み失敗:', error);
        }
    }
    
    observeYouTubeChanges() {
        // YouTube DOMの変更を監視
        const observer = new MutationObserver((mutations) => {
            let shouldCheck = false;
            
            mutations.forEach((mutation) => {
                // 新しいノードが追加された場合
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    for (let node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            // プレイヤーコントロール関連の要素が追加された場合
                            if (node.querySelector && (
                                node.querySelector('.ytp-chrome-bottom') ||
                                node.querySelector('.ytp-chrome-controls') ||
                                node.querySelector('[data-title-no-tooltip]') ||
                                node.classList.contains('ytp-chrome-bottom') ||
                                node.classList.contains('ytp-chrome-controls')
                            )) {
                                shouldCheck = true;
                                break;
                            }
                        }
                    }
                }
            });
            
            if (shouldCheck) {
                setTimeout(() => this.checkAndAddButton(), 500);
            }
        });
        
        // document全体を監視
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
        
        console.log('👁️ YouTube DOM監視開始');
    }
    
    checkAndAddButton() {
        // YouTube動画ページかどうか確認
        if (!this.isYouTubeVideoPage()) {
            return;
        }
        
        const currentVideoId = this.getCurrentVideoId();
        
        // 動画IDが変更された場合、既存ボタンを削除
        if (this.currentVideoId !== currentVideoId) {
            this.removeExistingButton();
            this.buttonAdded = false;
            this.currentVideoId = currentVideoId;
        }
        
        // ボタンが既に追加されている場合はスキップ
        if (this.buttonAdded) {
            return;
        }
        
        // ボタン挿入を試行
        this.insertTranscriptButton();
    }
    
    isYouTubeVideoPage() {
        const url = window.location.href;
        return url.includes('/watch') || url.includes('/shorts/');
    }
    
    getCurrentVideoId() {
        const url = window.location.href;
        const urlParams = new URLSearchParams(window.location.search);
        
        // 通常動画の場合
        if (url.includes('/watch')) {
            return urlParams.get('v');
        }
        
        // YouTube Shortsの場合
        if (url.includes('/shorts/')) {
            const match = url.match(/\/shorts\/([^?\/]+)/);
            return match ? match[1] : null;
        }
        
        return null;
    }
    
    insertTranscriptButton() {
        // 複数の挿入ポイントを試行（設定アイコン近くを優先）
        const insertionStrategies = [
            () => this.insertIntoPlayerSettings(),
            () => this.insertIntoControlsRight(),
            () => this.insertIntoTopLevelButtons(),
            () => this.insertIntoPlayerActions(),
            () => this.insertBelowPlayer()
        ];
        
        for (let strategy of insertionStrategies) {
            if (strategy()) {
                this.buttonAdded = true;
                console.log('✅ 字幕抽出ボタン追加成功');
                break;
            }
        }
        
        if (!this.buttonAdded) {
            console.warn('⚠️ ボタン挿入位置が見つかりませんでした');
            // フォールバック: 5秒後に再試行
            setTimeout(() => this.checkAndAddButton(), 5000);
        }
    }
    
    insertIntoPlayerSettings() {
        // YouTube設定ボタンの近くに挿入（最優先）
        const settingsButton = document.querySelector('.ytp-settings-button');
        const subtitlesButton = document.querySelector('.ytp-subtitles-button');
        
        // 設定ボタンまたは字幕ボタンの隣に配置
        const targetButton = settingsButton || subtitlesButton;
        if (targetButton && targetButton.parentNode) {
            const button = this.createTranscriptButton('player-settings');
            targetButton.parentNode.insertBefore(button, targetButton);
            console.log('📍 YouTube設定エリアに挿入');
            return true;
        }
        
        // 右コントロールエリア全体から設定系ボタンを探す
        const rightControls = document.querySelector('.ytp-right-controls');
        if (rightControls) {
            const button = this.createTranscriptButton('player-settings');
            // 設定ボタンの前に挿入（通常は最後の子要素）
            rightControls.appendChild(button);
            console.log('📍 右コントロールエリアに挿入');
            return true;
        }
        
        return false;
    }

    insertIntoControlsRight() {
        // プレイヤーコントロールの右側エリアに挿入
        const controlsRight = document.querySelector('.ytp-chrome-controls .ytp-right-controls');
        
        if (controlsRight) {
            const button = this.createTranscriptButton('player-control');
            controlsRight.insertBefore(button, controlsRight.firstChild);
            console.log('📍 プレイヤーコントロール右側に挿入');
            return true;
        }
        
        return false;
    }
    
    insertIntoTopLevelButtons() {
        // 動画タイトル下のボタンエリアに挿入
        const topLevelButtons = document.querySelector('#top-level-buttons-computed');
        
        if (topLevelButtons) {
            const button = this.createTranscriptButton('top-level');
            topLevelButtons.appendChild(button);
            console.log('📍 トップレベルボタンエリアに挿入');
            return true;
        }
        
        return false;
    }
    
    insertIntoPlayerActions() {
        // 動画情報エリアのアクションボタン群に挿入
        const actionsContainer = document.querySelector('#actions');
        
        if (actionsContainer) {
            const button = this.createTranscriptButton('action');
            actionsContainer.appendChild(button);
            console.log('📍 アクションコンテナに挿入');
            return true;
        }
        
        return false;
    }
    
    insertBelowPlayer() {
        // プレイヤーの直下に挿入（最後の手段）
        const player = document.querySelector('#movie_player') || document.querySelector('#player');
        
        if (player && player.parentNode) {
            const button = this.createTranscriptButton('below-player');
            
            // 専用コンテナを作成
            const container = document.createElement('div');
            container.className = 'yte-transcript-container';
            container.appendChild(button);
            
            player.parentNode.insertBefore(container, player.nextSibling);
            console.log('📍 プレイヤー下部に挿入');
            return true;
        }
        
        return false;
    }
    
    createTranscriptButton(type = 'default') {
        const button = document.createElement('button');
        button.id = 'yte-transcript-button';
        button.className = `yte-transcript-btn yte-transcript-btn-${type}`;
        
        // ボタンの外観設定（字幕特化アイコン）
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zM4 12h4v2H4v-2zm6 0h4v2h-4v-2zm6 0h4v2h-4v-2zM4 16h4v2H4v-2zm6 0h6v2h-6v-2z"/>
            </svg>
            <span class="yte-label">字幕抽出</span>
        `;
        
        button.title = 'YouTube字幕抽出 - AIで整形・要約';
        
        // クリックイベント
        button.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleButtonClick();
        });
        
        return button;
    }
    
    handleButtonClick() {
        const currentUrl = window.location.href;
        const videoId = this.getCurrentVideoId();
        
        if (!videoId) {
            this.showNotification('動画IDを取得できませんでした', 'error');
            return;
        }
        
        // ローディング状態表示
        this.showNotification('字幕抽出ツールを起動中...', 'loading');
        
        // 字幕抽出ツールを新しいタブで開く
        const extractUrl = `${this.serverUrl}?url=${encodeURIComponent(currentUrl)}&auto_extract=true`;
        
        try {
            window.open(extractUrl, '_blank', 'width=900,height=700,scrollbars=yes,resizable=yes');
            this.showNotification('字幕抽出ツールを起動しました', 'success');
        } catch (error) {
            console.error('字幕抽出ツール起動エラー:', error);
            this.showNotification('字幕抽出ツールの起動に失敗しました', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // 既存の通知を削除
        const existingNotification = document.querySelector('.yte-notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        // 通知要素を作成
        const notification = document.createElement('div');
        notification.className = `yte-notification yte-notification-${type}`;
        notification.innerHTML = `
            <div class="yte-notification-content">
                <span class="yte-notification-icon">
                    ${type === 'loading' ? '🔄' : type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="yte-notification-message">${message}</span>
            </div>
        `;
        
        // ページに追加
        document.body.appendChild(notification);
        
        // 自動削除（エラー以外）
        if (type !== 'error') {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 3000);
        }
    }
    
    removeExistingButton() {
        const existingButton = document.querySelector('#yte-transcript-button');
        if (existingButton) {
            existingButton.remove();
        }
        
        const existingContainer = document.querySelector('.yte-transcript-container');
        if (existingContainer) {
            existingContainer.remove();
        }
    }
}

// 拡張機能初期化
let transcriptExtractor;

// DOM準備完了後に初期化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        transcriptExtractor = new YouTubeTranscriptExtractor();
    });
} else {
    transcriptExtractor = new YouTubeTranscriptExtractor();
}

// YouTube SPA navigation イベントリスナー
window.addEventListener('yt-navigate-finish', () => {
    if (transcriptExtractor) {
        setTimeout(() => transcriptExtractor.checkAndAddButton(), 1000);
    }
});

// エクスポート（テスト用）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeTranscriptExtractor;
}