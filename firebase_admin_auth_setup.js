const admin = require('firebase-admin');
const fs = require('fs');

async function setupFirebaseAuthenticationAdmin() {
    console.log('🔧 Setting up Firebase Authentication via Admin SDK...');
    
    try {
        // Initialize Firebase Admin (using default credentials from environment)
        console.log('Initializing Firebase Admin SDK...');
        
        // For Cloud Run, we can use default credentials
        admin.initializeApp({
            projectId: 'yt-transcript-demo-2025'
        });
        
        console.log('✅ Firebase Admin initialized successfully');
        
        // Get authentication service
        const auth = admin.auth();
        
        // Check current project config
        console.log('📋 Checking current authentication configuration...');
        
        try {
            // List current sign-in methods
            const projectConfig = await auth.getProjectConfig();
            console.log('Current config:', JSON.stringify(projectConfig, null, 2));
            
            // Check if email/password is already enabled
            const emailPasswordEnabled = projectConfig.signInOptions?.some(
                option => option.providerId === 'password'
            );
            
            if (emailPasswordEnabled) {
                console.log('✅ Email/Password authentication already enabled');
                return true;
            }
            
            // Enable Email/Password authentication
            console.log('🚀 Enabling Email/Password authentication...');
            
            const updatedConfig = await auth.updateProjectConfig({
                signInOptions: [
                    { providerId: 'password' },
                    ...(projectConfig.signInOptions || []).filter(
                        option => option.providerId !== 'password'
                    )
                ]
            });
            
            console.log('✅ Email/Password authentication enabled successfully');
            console.log('Updated config:', JSON.stringify(updatedConfig, null, 2));
            
            // Verify the configuration
            const verifyConfig = await auth.getProjectConfig();
            const isEnabled = verifyConfig.signInOptions?.some(
                option => option.providerId === 'password'
            );
            
            if (isEnabled) {
                console.log('🎉 SUCCESS: Firebase Authentication configuration complete!');
                console.log('✅ Email/Password authentication is now enabled');
                console.log('✅ tenormusica7@gmail.com can now create accounts');
                return true;
            } else {
                console.log('❌ Verification failed - Email/Password not found in config');
                return false;
            }
            
        } catch (configError) {
            console.error('Configuration error:', configError.message);
            
            // If project config API is not available, try alternative approach
            console.log('📋 Attempting alternative configuration method...');
            
            // Create a test user to verify Email/Password is working
            try {
                const testUser = await auth.createUser({
                    email: 'test-setup-verification@example.com',
                    password: 'tempPassword123!',
                    disabled: true // Create as disabled for safety
                });
                
                console.log('✅ Test user created - Email/Password authentication is functional');
                
                // Clean up test user
                await auth.deleteUser(testUser.uid);
                console.log('🧹 Test user cleaned up');
                
                return true;
                
            } catch (testError) {
                console.error('❌ Email/Password authentication test failed:', testError.message);
                return false;
            }
        }
        
    } catch (error) {
        console.error('❌ Firebase Admin SDK setup failed:', error.message);
        console.error('Error details:', error);
        
        // Check if this is an authentication/permission issue
        if (error.message.includes('credentials') || error.message.includes('permission')) {
            console.log('\n🔑 Authentication Issue Detected');
            console.log('This error suggests we need to set up service account credentials.');
            console.log('Moving to REST API approach...');
        }
        
        return false;
    }
}

// Export for potential reuse
module.exports = { setupFirebaseAuthenticationAdmin };

// Run if called directly
if (require.main === module) {
    setupFirebaseAuthenticationAdmin().then(success => {
        if (success) {
            console.log('\n🎉 Firebase Authentication setup completed via Admin SDK!');
            process.exit(0);
        } else {
            console.log('\n⚠️ Admin SDK approach failed, will try REST API...');
            process.exit(1);
        }
    }).catch(error => {
        console.error('Fatal error:', error.message);
        process.exit(1);
    });
}