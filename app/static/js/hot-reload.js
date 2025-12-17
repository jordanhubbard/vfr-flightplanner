/**
 * Hot Reload Client
 * 
 * Automatically refreshes the browser when the server restarts in development mode.
 * Uses a simple polling mechanism to detect server availability.
 */

(function() {
    'use strict';
    
    // Only enable in development (check if running on localhost)
    const isDevelopment = window.location.hostname === 'localhost' || 
                          window.location.hostname === '127.0.0.1' ||
                          window.location.hostname === '';
    
    if (!isDevelopment) {
        return;
    }
    
    let isServerDown = false;
    let checkInterval = null;
    let consecutiveFailures = 0;
    const MAX_FAILURES = 3;
    
    // Show reload notification
    function showReloadNotification() {
        const notification = document.createElement('div');
        notification.id = 'hot-reload-notification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideIn 0.3s ease-out;
        `;
        
        notification.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2C5.58 2 2 5.58 2 10s3.58 8 8 8 8-3.58 8-8-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z" fill="white"/>
                <path d="M10 6v5l4 2" stroke="white" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span>Changes detected - Reloading...</span>
        `;
        
        // Add animation keyframes
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from {
                    transform: translateX(400px);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
        `;
        document.head.appendChild(style);
        document.body.appendChild(notification);
    }
    
    // Check if server is available
    async function checkServer() {
        try {
            const response = await fetch('/api/health', {
                method: 'GET',
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (response.ok) {
                consecutiveFailures = 0;
                
                if (isServerDown) {
                    // Server is back up after being down - reload the page
                    console.log('[Hot Reload] Server is back online. Reloading page...');
                    showReloadNotification();
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
                
                isServerDown = false;
            } else {
                throw new Error('Server responded with error');
            }
        } catch (error) {
            consecutiveFailures++;
            
            if (consecutiveFailures >= MAX_FAILURES && !isServerDown) {
                console.log('[Hot Reload] Server appears to be restarting...');
                isServerDown = true;
            }
        }
    }
    
    // Start monitoring
    function startMonitoring() {
        console.log('[Hot Reload] Development mode detected. Hot reload active.');
        
        // Check every 1 second
        checkInterval = setInterval(checkServer, 1000);
        
        // Initial check
        checkServer();
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startMonitoring);
    } else {
        startMonitoring();
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (checkInterval) {
            clearInterval(checkInterval);
        }
    });
})();
