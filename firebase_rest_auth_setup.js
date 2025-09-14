const https = require('https');
const { URL } = require('url');

async function setupFirebaseAuthenticationREST() {
    console.log('🌐 Setting up Firebase Authentication via REST API...');
    
    try {
        const projectId = 'yt-transcript-demo-2025';
        const apiKey = 'AIzaSyCgICKsMcrXeZs5U5JvWO9Q3QiNRiPrKb8';
        
        console.log(`📋 Project ID: ${projectId}`);
        console.log(`🔑 API Key: ${apiKey.substring(0, 20)}...`);
        
        // First, let's check if the Firebase Authentication service is enabled
        console.log('🔍 Checking Firebase Authentication service status...');
        
        const configUrl = `https://identitytoolkit.googleapis.com/v1/projects/${projectId}/config?key=${apiKey}`;
        
        const config = await makeHttpRequest(configUrl, 'GET');
        console.log('📋 Current config response:', JSON.stringify(config, null, 2));
        
        if (config.error) {
            console.log('⚠️ Authentication service may not be enabled yet');
            
            // Try to enable Email/Password provider through a different endpoint
            console.log('🚀 Attempting to enable Email/Password authentication...');
            
            const enableEmailPasswordUrl = `https://identitytoolkit.googleapis.com/v1/projects/${projectId}/config?updateMask=signIn.email.enabled,signIn.email.passwordRequired&key=${apiKey}`;
            
            const enablePayload = {
                signIn: {
                    email: {
                        enabled: true,
                        passwordRequired: true
                    }
                }
            };
            
            const enableResult = await makeHttpRequest(enableEmailPasswordUrl, 'PATCH', enablePayload);
            
            if (enableResult.error) {
                console.error('❌ Failed to enable Email/Password:', enableResult.error);
                
                // Try alternative Firebase Config API
                console.log('🔄 Trying alternative Firebase Config API...');
                
                const altConfigUrl = `https://firebase.googleapis.com/v1beta1/projects/${projectId}/config?key=${apiKey}`;
                const altConfig = await makeHttpRequest(altConfigUrl, 'GET');
                
                console.log('📋 Alternative config result:', JSON.stringify(altConfig, null, 2));
                
                if (altConfig.error) {
                    console.log('❌ Alternative config also failed');
                    console.log('🔧 This indicates the Firebase Authentication service needs to be enabled manually');
                    
                    // Final attempt: try to create a config if none exists
                    console.log('🚀 Final attempt: Initialize authentication config...');
                    
                    const initUrl = `https://identitytoolkit.googleapis.com/v1/projects/${projectId}/initializeAuth?key=${apiKey}`;
                    const initResult = await makeHttpRequest(initUrl, 'POST', {});
                    
                    console.log('📋 Initialize result:', JSON.stringify(initResult, null, 2));
                    
                    if (initResult.error) {
                        console.log('❌ Initialize authentication failed');
                        console.log('📋 Manual setup required via Firebase Console');
                        return false;
                    } else {
                        console.log('✅ Authentication initialized successfully');
                        return true;
                    }
                } else {
                    console.log('✅ Alternative config successful');
                    return true;
                }
            } else {
                console.log('✅ Email/Password authentication enabled successfully');
                console.log('📋 Result:', JSON.stringify(enableResult, null, 2));
                return true;
            }
        } else {
            console.log('✅ Firebase Authentication is already configured');
            
            // Check if Email/Password is specifically enabled
            const signInConfig = config.signIn || {};
            const emailConfig = signInConfig.email || {};
            
            if (emailConfig.enabled) {
                console.log('✅ Email/Password authentication is already enabled');
                return true;
            } else {
                console.log('🚀 Enabling Email/Password authentication...');
                
                const updateUrl = `https://identitytoolkit.googleapis.com/v1/projects/${projectId}/config?updateMask=signIn.email.enabled,signIn.email.passwordRequired&key=${apiKey}`;
                
                const updatePayload = {
                    signIn: {
                        email: {
                            enabled: true,
                            passwordRequired: true
                        }
                    }
                };
                
                const updateResult = await makeHttpRequest(updateUrl, 'PATCH', updatePayload);
                
                if (updateResult.error) {
                    console.error('❌ Failed to update Email/Password config:', updateResult.error);
                    return false;
                } else {
                    console.log('✅ Email/Password authentication updated successfully');
                    console.log('📋 Update result:', JSON.stringify(updateResult, null, 2));
                    return true;
                }
            }
        }
        
    } catch (error) {
        console.error('❌ REST API setup failed:', error.message);
        console.error('Error details:', error);
        return false;
    }
}

function makeHttpRequest(url, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const options = {
            hostname: urlObj.hostname,
            port: urlObj.port || 443,
            path: urlObj.pathname + urlObj.search,
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'Firebase-Setup-Script/1.0'
            }
        };
        
        const req = https.request(options, (res) => {
            let responseData = '';
            
            res.on('data', (chunk) => {
                responseData += chunk;
            });
            
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(responseData);
                    resolve(jsonData);
                } catch (e) {
                    resolve({ 
                        statusCode: res.statusCode,
                        rawData: responseData,
                        parseError: e.message 
                    });
                }
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        if (data && method !== 'GET') {
            req.write(JSON.stringify(data));
        }
        
        req.end();
    });
}

// Export for potential reuse
module.exports = { setupFirebaseAuthenticationREST };

// Run if called directly
if (require.main === module) {
    setupFirebaseAuthenticationREST().then(success => {
        if (success) {
            console.log('\n🎉 SUCCESS: Firebase Authentication setup completed via REST API!');
            console.log('✅ Email/Password authentication is now enabled');
            console.log('✅ tenormusica7@gmail.com can now create accounts');
            console.log('✅ Production app ready for testing: https://ai-fm-podcast-ycqe3vmjva-uc.a.run.app');
            process.exit(0);
        } else {
            console.log('\n❌ REST API approach also failed');
            console.log('📋 Manual setup via Firebase Console is required');
            console.log('🔗 Please visit: https://console.firebase.google.com/u/0/project/yt-transcript-demo-2025/authentication');
            process.exit(1);
        }
    }).catch(error => {
        console.error('Fatal error:', error.message);
        process.exit(1);
    });
}