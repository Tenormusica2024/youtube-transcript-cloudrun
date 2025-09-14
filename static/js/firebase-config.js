// Firebase Configuration and Authentication Module
import { initializeApp } from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-app.js';
import { 
    getAuth, 
    signInWithEmailAndPassword, 
    createUserWithEmailAndPassword, 
    signOut, 
    onAuthStateChanged 
} from 'https://www.gstatic.com/firebasejs/9.23.0/firebase-auth.js';

// Firebase Configuration
// 
const firebaseConfig = {
    apiKey: "AIzaSyCceHAg85kW2w7PPI-2Otx21wfo_TgSIyg",
    authDomain: "yt-transcript-demo-2025.firebaseapp.com",
    projectId: "yt-transcript-demo-2025",
    storageBucket: "yt-transcript-demo-2025.appspot.com",
    messagingSenderId: "72885249208",
    appId: "1:72885249208:web:2c1c9f0d8f3c4e5f6g7h8i"
};

// Cloud Run URL - PRODUCTION: run.app uses Firebase Auth
const isDevelopment = window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1';

// Firebase
let app, auth;

if (!isDevelopment) {
    // Firebase
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
} else {
    // 
    console.log(' Development mode: Firebase initialization skipped');
    app = null;
    auth = null;
}

// 
let currentUser = null;
let authStateListeners = [];

// 
const AUTH_STORAGE_KEY = 'ai_fm_podcast_auth';

// 
function restoreAuthState() {
    try {
        const storedAuth = localStorage.getItem(AUTH_STORAGE_KEY);
        if (storedAuth) {
            const authData = JSON.parse(storedAuth);
            console.log(' Restoring authentication state from localStorage');
            
            // 
            if (isDevelopment && authData.isDevelopment) {
                const userUID = `user_${authData.email.replace(/[^a-zA-Z0-9]/g, '_')}_dev`;
                
                currentUser = {
                    uid: userUID,
                    email: authData.email,
                    displayName: authData.displayName || authData.email.split('@')[0],
                    getIdToken: async () => {
                        const userData = btoa(JSON.stringify({
                            uid: userUID,
                            email: authData.email,
                            displayName: authData.displayName || authData.email.split('@')[0]
                        }));
                        return `mock-token-for-development:${userData}`;
                    },
                    emailVerified: true
                };
                
                console.log(' Development authentication state restored:', currentUser.email);
                authStateListeners.forEach(callback => callback(currentUser));
                return true;
            }
        }
    } catch (error) {
        console.warn(' Failed to restore auth state from localStorage:', error);
        localStorage.removeItem(AUTH_STORAGE_KEY);
    }
    return false;
}

// 
function saveAuthState(user) {
    try {
        if (user && isDevelopment) {
            const authData = {
                email: user.email,
                displayName: user.displayName,
                uid: user.uid,
                isDevelopment: true,
                timestamp: Date.now()
            };
            localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData));
            console.log(' Authentication state saved to localStorage');
        }
    } catch (error) {
        console.warn(' Failed to save auth state to localStorage:', error);
    }
}

// 
function clearAuthState() {
    try {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        console.log(' Authentication state cleared from localStorage');
    } catch (error) {
        console.warn(' Failed to clear auth state from localStorage:', error);
    }
}

// 
function completeSignOut() {
    try {
        console.log(' Performing complete sign out cleanup');
        
        // 
        clearAuthState();
        
        // 
        currentUser = null;
        
        // 
        const authRelatedKeys = [
            'ai_fm_podcast_auth',
            'firebase:authUser',
            'firebase:host'
        ];
        
        authRelatedKeys.forEach(key => {
            try {
                localStorage.removeItem(key);
                console.log(` Cleared localStorage key: ${key}`);
            } catch (error) {
                console.warn(` Failed to clear ${key}:`, error);
            }
        });
        
        console.log(' Complete sign out cleanup finished');
    } catch (error) {
        console.error(' Error during complete sign out:', error);
    }
}

// 
// 
// if (isDevelopment) {
//     restoreAuthState();
// }

// 
if (isDevelopment) {
    console.log(' Clearing any existing auth state on page load');
    completeSignOut();
}

// 
if (auth) {
    onAuthStateChanged(auth, (user) => {
        currentUser = user;
        if (user) {
            saveAuthState(user);
        } else {
            clearAuthState();
        }
        authStateListeners.forEach(callback => callback(user));
    });
}

// API
export const firebaseAuth = {
    // 
    getCurrentUser: () => currentUser,
    
    // 
    onAuthStateChanged: (callback) => {
        authStateListeners.push(callback);
        // 
        if (currentUser !== undefined) {
            callback(currentUser);
        }
    },
    
    // 
    signIn: async (email, password) => {
        try {
            console.log(' Starting sign in process for:', email);
            
            // 
            if (isDevelopment) {
                console.log(' Using development mode authentication');
                return await debugHelper.mockSignIn(email, password);
            }
            
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            console.log(' Sign in successful:', userCredential.user.email);
            return userCredential.user;
        } catch (error) {
            console.error(' Sign in error:', error);
            console.error('Error code:', error.code);
            console.error('Error message:', error.message);
            throw new Error(getErrorMessage(error.code));
        }
    },
    
    // 
    signUp: async (email, password) => {
        try {
            console.log(' Starting sign up process for:', email);
            
            // 
            if (isDevelopment) {
                console.log(' Using development mode authentication');
                return await debugHelper.mockSignUp(email, password);
            }
            
            const userCredential = await createUserWithEmailAndPassword(auth, email, password);
            console.log(' Sign up successful:', userCredential.user.email);
            return userCredential.user;
        } catch (error) {
            console.error(' Sign up error:', error);
            console.error('Error code:', error.code);
            console.error('Error message:', error.message);
            throw new Error(getErrorMessage(error.code));
        }
    },
    
    // 
    signOut: async () => {
        try {
            console.log(' Starting sign out process');
            
            // 
            completeSignOut();
            
            // 
            authStateListeners.forEach(callback => {
                try {
                    callback(null);
                } catch (error) {
                    console.error('Error in auth state listener:', error);
                }
            });
            
            if (isDevelopment) {
                // 
                console.log(' Development mode: Mock sign out completed');
                return;
            }
            
            // Firebase
            if (auth) {
                await signOut(auth);
            }
            
            console.log(' Sign out completed successfully');
        } catch (error) {
            console.error(' Sign out error:', error);
            // 
            completeSignOut();
            authStateListeners.forEach(callback => {
                try {
                    callback(null);
                } catch (listenerError) {
                    console.error('Error in auth state listener during error handling:', listenerError);
                }
            });
            throw new Error('');
        }
    },
    
    // ID
    getIdToken: async () => {
        if (!currentUser) {
            throw new Error('');
        }
        try {
            // 
            if (isDevelopment && currentUser.getIdToken) {
                return await currentUser.getIdToken();
            }
            // Firebase
            return await currentUser.getIdToken();
        } catch (error) {
            console.error('ID token error:', error);
            throw new Error('');
        }
    }
};

// 
function getErrorMessage(errorCode) {
    const errorMessages = {
        'auth/user-not-found': '',
        'auth/wrong-password': '',
        'auth/email-already-in-use': '',
        'auth/weak-password': '6',
        'auth/invalid-email': '',
        'auth/too-many-requests': '',
        'auth/network-request-failed': '',
        'auth/internal-error': ''
    };
    
    return errorMessages[errorCode] || '';
}

// API
export const apiClient = {
    // API
    request: async (url, options = {}) => {
        try {
            // URLパラメータの処理
            let finalUrl = url;
            if (options.params) {
                const searchParams = new URLSearchParams(options.params);
                finalUrl = `${url}?${searchParams}`;
            }
            
            console.log(' API Request:', { url: finalUrl, method: options.method || 'GET' });
            
            // 🔥 FIX: 認証状態チェックを柔軟にする - 削除機能等で非認証でも利用可能
            let token = null;
            if (currentUser) {
                try {
                    token = await firebaseAuth.getIdToken();
                    console.log(' Token obtained:', token ? 'Yes' : 'No');
                } catch (error) {
                    console.warn('⚠️ Failed to get auth token:', error);
                    token = null;
                }
            } else {
                console.log('⚠️ No authenticated user - proceeding without token for non-auth endpoints');
            }
            
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };
            
            // 🔥 FIX: tokenがある場合のみAuthorizationヘッダーを追加
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
            
            // paramsはfetchオプションから除外
            const fetchOptions = { ...options };
            delete fetchOptions.params;
            
            const response = await fetch(finalUrl, {
                ...fetchOptions,
                headers
            });
            
            console.log(' Response status:', response.status, response.statusText);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error(' Response error body:', errorText);
                
                let errorData = {};
                try {
                    errorData = JSON.parse(errorText);
                } catch (e) {
                    console.warn('Could not parse error response as JSON');
                    errorData = { error: errorText || `HTTP ${response.status}: ${response.statusText}` };
                }
                
                const error = new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
                error.status = response.status;
                error.response = errorData;
                throw error;
            }
            
            const responseData = await response.json();
            console.log(' API Response data:', responseData);
            return responseData;
        } catch (error) {
            console.error(' API request error:', error);
            console.error('Error details:', {
                message: error.message,
                status: error.status,
                stack: error.stack
            });
            throw error;
        }
    },
    
    // MP3Signed URL
    getUploadUrl: async (filename, contentType, fileSize) => {
        return await apiClient.request('/api/upload/signed-url', {
            method: 'POST',
            body: JSON.stringify({
                filename: filename,
                contentType: contentType,
                fileSize: fileSize
            })
        });
    },
    
    // 
    createTrack: async (trackData) => {
        return await apiClient.request('/api/tracks', {
            method: 'POST',
            body: JSON.stringify(trackData)
        });
    },
    
    // 
    getTracks: async (params = {}) => {
        return await apiClient.request(`/api/tracks`, {
            method: 'GET',
            params: params
        });
    },
    
    // URL
    getPlayUrl: async (trackId) => {
        return await apiClient.request(`/api/tracks/${trackId}/play-url`);
    }
};

// 
export const uploadHelper = {
    // GCS
    uploadToGCS: async (signedUrl, file, onProgress = null) => {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            // 
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Upload failed due to network error'));
            });
            
            xhr.open('PUT', signedUrl);
            xhr.setRequestHeader('Content-Type', file.type);
            xhr.send(file);
        });
    },
    
    // 
    uploadDirect: async (uploadData, file, onProgress = null) => {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('objectName', uploadData.objectName);
            formData.append('uploadId', uploadData.uploadId);
            
            const xhr = new XMLHttpRequest();
            
            // 
            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        const percentComplete = (e.loaded / e.total) * 100;
                        onProgress(percentComplete);
                    }
                });
            }
            
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve();
                } else {
                    reject(new Error(`Direct upload failed: ${xhr.status} ${xhr.statusText}`));
                }
            });
            
            xhr.addEventListener('error', () => {
                reject(new Error('Direct upload failed due to network error'));
            });
            
            // 
            firebaseAuth.getIdToken().then(token => {
                xhr.open('POST', uploadData.uploadEndpoint);
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
                xhr.send(formData);
            }).catch(error => {
                reject(new Error('Failed to get auth token: ' + error.message));
            });
        });
    },
    
    // 
    extractAudioMetadata: (file) => {
        return new Promise((resolve) => {
            const audio = document.createElement('audio');
            const url = URL.createObjectURL(file);
            
            audio.addEventListener('loadedmetadata', () => {
                resolve({
                    duration: audio.duration,
                    sampleRate: audio.sampleRate || 44100
                });
                URL.revokeObjectURL(url);
            });
            
            audio.addEventListener('error', () => {
                // 
                resolve({
                    duration: 0,
                    sampleRate: 44100
                });
                URL.revokeObjectURL(url);
            });
            
            audio.src = url;
        });
    },
    
    // 
    extractMediaMetadata: (file) => {
        return new Promise((resolve) => {
            const isVideo = file.type.startsWith('video/');
            const element = document.createElement(isVideo ? 'video' : 'audio');
            const url = URL.createObjectURL(file);
            
            element.addEventListener('loadedmetadata', () => {
                const metadata = {
                    duration: element.duration,
                    mediaType: isVideo ? 'video' : 'audio'
                };
                
                if (isVideo) {
                    metadata.width = element.videoWidth;
                    metadata.height = element.videoHeight;
                } else {
                    metadata.sampleRate = element.sampleRate || 44100;
                }
                
                resolve(metadata);
                URL.revokeObjectURL(url);
            });
            
            element.addEventListener('error', () => {
                // 
                const metadata = {
                    duration: 0,
                    mediaType: isVideo ? 'video' : 'audio'
                };
                
                if (isVideo) {
                    metadata.width = 0;
                    metadata.height = 0;
                } else {
                    metadata.sampleRate = 44100;
                }
                
                resolve(metadata);
                URL.revokeObjectURL(url);
            });
            
            element.src = url;
        });
    },
    
    // 
    extractArtwork: async (file) => {
        if (!file.type.startsWith('audio/')) {
            return null;
        }
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const token = await firebaseAuth.getIdToken();
            
            const response = await fetch('/api/extract-artwork', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });
            
            if (!response.ok) {
                console.warn('Failed to extract artwork:', response.statusText);
                return null;
            }
            
            const data = await response.json();
            return data.artwork || null;
        } catch (error) {
            console.warn('Error extracting artwork:', error);
            return null;
        }
    }
};

// 
export const debugHelper = {
    // 
    simulateAuth: (email = 'test@example.com') => {
        currentUser = {
            uid: 'mock-user-dev',  // Fixed UID to match backend
            email: email,
            displayName: email.split('@')[0],
            getIdToken: async () => 'mock-token-for-development'
        };
        
        authStateListeners.forEach(callback => callback(currentUser));
        console.log('DEBUG: Simulated authentication for:', email);
    },
    
    // 
    mockSignIn: async (email, password) => {
        console.log(' Mock sign in for:', email);
        
        // 
        if (!email || !password) {
            throw new Error('');
        }
        
        if (!email.includes('@')) {
            throw new Error('');
        }
        
        // 
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // UID
        // UID
        const userUID = `user_${email.replace(/[^a-zA-Z0-9]/g, '_')}_dev`;
        
        const mockUser = {
            uid: userUID,
            email: email,
            displayName: email.split('@')[0],
            getIdToken: async () => {
                // 
                const userData = btoa(JSON.stringify({
                    uid: userUID,
                    email: email,
                    displayName: email.split('@')[0]
                }));
                return `mock-token-for-development:${userData}`;
            },
            emailVerified: true
        };
        
        currentUser = mockUser;
        
        // 
        saveAuthState(mockUser);
        
        authStateListeners.forEach(callback => callback(currentUser));
        
        // 
        try {
            await apiClient.request('/api/users/profile', {
                method: 'POST',
                body: JSON.stringify({
                    displayName: mockUser.displayName,
                    bio: ''
                })
            });
            console.log(' User profile created/updated automatically');
        } catch (error) {
            console.warn(' Failed to auto-create user profile:', error);
        }
        
        console.log(' Mock sign in successful');
        return mockUser;
    },
    
    // 
    mockSignUp: async (email, password) => {
        console.log(' Mock sign up for:', email);
        
        // 
        if (!email || !password) {
            throw new Error('');
        }
        
        if (!email.includes('@')) {
            throw new Error('');
        }
        
        if (password.length < 6) {
            throw new Error('6');
        }
        
        // 
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        // UID
        // UID
        const userUID = `user_${email.replace(/[^a-zA-Z0-9]/g, '_')}_dev`;
        
        const mockUser = {
            uid: userUID,
            email: email,
            displayName: email.split('@')[0],
            getIdToken: async () => {
                // 
                const userData = btoa(JSON.stringify({
                    uid: userUID,
                    email: email,
                    displayName: email.split('@')[0]
                }));
                return `mock-token-for-development:${userData}`;
            },
            emailVerified: false
        };
        
        currentUser = mockUser;
        
        // 
        saveAuthState(mockUser);
        
        authStateListeners.forEach(callback => callback(currentUser));
        
        // 
        try {
            await apiClient.request('/api/users/profile', {
                method: 'POST',
                body: JSON.stringify({
                    displayName: mockUser.displayName,
                    bio: `${mockUser.displayName}`
                })
            });
            console.log(' New user profile created automatically');
        } catch (error) {
            console.warn(' Failed to auto-create user profile:', error);
        }
        
        console.log(' Mock sign up successful');
        return mockUser;
    },
    
    // 
    resetAuth: () => {
        clearAuthState();
        currentUser = null;
        authStateListeners.forEach(callback => callback(null));
        console.log('DEBUG: Authentication reset');
    }
};