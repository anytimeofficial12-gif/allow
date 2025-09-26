/**
 * Configuration file for ANYTIME Contest Landing Page
 * 
 * This file contains all configurable settings for the application.
 * Update these values based on your deployment environment.
 */

// Backend API Configuration
const CONFIG = {
    // Backend URL - Update this when deploying
    // For local development: 'http://localhost:8000'
    // For production: Direct connection to Render backend
    API_BASE_URL: (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
        ? 'http://localhost:8000'  // Local development
        : '/api',  // Production: same-origin proxy via vercel.json rewrite to backend
    
    // Application settings
    APP_NAME: 'ANYTIME',
    CONTEST_TITLE: 'Guess what we do & Win ₹500',
    CONTEST_SUBTITLE: 'Be among the first to discover what we\'re building. Top 10 accurate guesses win!',
    
    // Form settings
    FORM_VALIDATION: {
        MIN_NAME_LENGTH: 2,
        MIN_ANSWER_LENGTH: 5,
        EMAIL_PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    },
    
    // UI settings
    ANIMATION_DELAY: 2000, // Delay before showing terms modal (ms)
    NOTIFICATION_DURATION: 4000, // How long notifications stay visible (ms)
    
    // Debug settings (set to false in production)
    DEBUG_MODE: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} else {
    window.CONFIG = CONFIG;
}
