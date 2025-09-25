// DOM Elements
const privacyModal = document.getElementById('privacyModal');
const acceptBtn = document.getElementById('acceptBtn');
const declineBtn = document.getElementById('declineBtn');
const formContainer = document.getElementById('formContainer');
const contestForm = document.getElementById('contestForm');
const submitBtn = document.getElementById('submitBtn');
const declineMessage = document.getElementById('declineMessage');
const successMessage = document.getElementById('successMessage');
const nameInput = document.getElementById('name');
const emailInput = document.getElementById('email');
const answerInput = document.getElementById('answer');

// Configuration - Backend URL
// Uses CONFIG from config.js for easy deployment management
const API_BASE_URL = CONFIG.API_BASE_URL;

// State management
let termsAccepted = false;
let formSubmitted = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    if (CONFIG.DEBUG_MODE) {
        console.log('DOM loaded, initializing app...'); // Debug log
        console.log('Form container:', formContainer); // Debug log
        console.log('Accept button:', acceptBtn); // Debug log
        console.log('API Base URL:', API_BASE_URL); // Debug log
    }
    
    // Show privacy modal after configured delay
    setTimeout(() => {
        showPrivacyModal();
    }, CONFIG.ANIMATION_DELAY);

    // Set up event listeners
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    // Modal buttons
    if (acceptBtn) {
        acceptBtn.addEventListener('click', acceptTerms);
        if (CONFIG.DEBUG_MODE) console.log('Accept button event listener added'); // Debug log
    } else {
        console.error('Accept button not found!'); // Debug log
    }
    
    if (declineBtn) {
        declineBtn.addEventListener('click', declineTerms);
        if (CONFIG.DEBUG_MODE) console.log('Decline button event listener added'); // Debug log
    } else {
        console.error('Decline button not found!'); // Debug log
    }
    
    // Form submission
    contestForm.addEventListener('submit', handleFormSubmit);
    
    // Input validation
    nameInput.addEventListener('input', validateName);
    emailInput.addEventListener('input', validateEmail);
    answerInput.addEventListener('input', validateAnswer);
    
    // Close modal when clicking outside
    privacyModal.addEventListener('click', function(e) {
        if (e.target === privacyModal) {
            // Don't close modal on outside click - user must make a choice
        }
    });
}

// Privacy Modal Functions
function showPrivacyModal() {
    privacyModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function hidePrivacyModal() {
    privacyModal.classList.remove('show');
    document.body.style.overflow = 'auto';
}

function acceptTerms() {
    if (CONFIG.DEBUG_MODE) console.log('Accept button clicked'); // Debug log
    termsAccepted = true;
    if (CONFIG.DEBUG_MODE) console.log('Terms accepted:', termsAccepted); // Debug log
    hidePrivacyModal();
    
    // Hide decline message immediately
    declineMessage.style.display = 'none';
    
    // Show form immediately after accepting terms
    showForm();
    
    // Also try again after a short delay as a fallback
    setTimeout(() => {
        if (termsAccepted && !formContainer.classList.contains('show')) {
            if (CONFIG.DEBUG_MODE) console.log('Fallback: showing form again'); // Debug log
            showForm();
        }
    }, 200);
}

function declineTerms() {
    termsAccepted = false;
    hidePrivacyModal();
    showDeclineMessage();
    disableForm();
}

// Form Functions
function showForm() {
    if (termsAccepted) {
        formContainer.classList.add('show');
        declineMessage.style.display = 'none';
        enableForm(); // Make sure form is enabled
        if (CONFIG.DEBUG_MODE) {
            console.log('Form should now be visible'); // Debug log
            console.log('Form container classes:', formContainer.className); // Debug log
            console.log('Form container style:', window.getComputedStyle(formContainer).opacity); // Debug log
        }
    } else {
        if (CONFIG.DEBUG_MODE) console.log('Terms not accepted, form not shown'); // Debug log
    }
}

function showDeclineMessage() {
    formContainer.classList.add('show');
    declineMessage.style.display = 'block';
}

function disableForm() {
    nameInput.disabled = true;
    emailInput.disabled = true;
    answerInput.disabled = true;
    submitBtn.disabled = true;
    submitBtn.textContent = 'Terms Not Accepted';
}

function enableForm() {
    nameInput.disabled = false;
    emailInput.disabled = false;
    answerInput.disabled = false;
    submitBtn.disabled = false;
    submitBtn.textContent = 'JEET JAAUNGA 😏';
    
    // Ensure decline message is hidden
    declineMessage.style.display = 'none';
    
    if (CONFIG.DEBUG_MODE) console.log('Form enabled, decline message hidden'); // Debug log
}

// Validation Functions
function validateName() {
    const name = nameInput.value.trim();
    if (name.length < CONFIG.FORM_VALIDATION.MIN_NAME_LENGTH) {
        nameInput.style.borderColor = '#ff6b6b';
        return false;
    } else {
        nameInput.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        return true;
    }
}

function validateEmail() {
    const email = emailInput.value.trim();
    const emailPattern = CONFIG.FORM_VALIDATION.EMAIL_PATTERN;
    
    if (emailPattern.test(email)) {
        emailInput.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        return true;
    } else {
        emailInput.style.borderColor = '#ff6b6b';
        return false;
    }
}

function validateAnswer() {
    const answer = answerInput.value.trim();
    if (answer.length >= CONFIG.FORM_VALIDATION.MIN_ANSWER_LENGTH) {
        answerInput.style.borderColor = 'rgba(255, 255, 255, 0.1)';
        return true;
    } else {
        answerInput.style.borderColor = '#ff6b6b';
        return false;
    }
}

function validateForm() {
    const isNameValid = validateName();
    const isEmailValid = validateEmail();
    const isAnswerValid = validateAnswer();
    
    return isNameValid && isEmailValid && isAnswerValid;
}

// Form Submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!termsAccepted) {
        showDeclineMessage();
        return;
    }
    
    if (!validateForm()) {
        showNotification('Please fill in all fields correctly', 'error');
        return;
    }
    
    if (formSubmitted) {
        return;
    }
    
    // Disable form during submission
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="loading-spinner"></span> Submitting...';
    
    // Add loading class for styling
    submitBtn.classList.add('loading');
    
    try {
        const formData = {
            name: nameInput.value.trim(),
            email: emailInput.value.trim(),
            answer: answerInput.value.trim()
        };
        
        // Send POST request to /submit
        const response = await fetch(`${API_BASE_URL}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const result = await response.json();
            formSubmitted = true;
            showSuccessMessage();
            if (CONFIG.DEBUG_MODE) console.log('Submission successful:', result);
        } else {
            // Try to parse FastAPI/Pydantic validation errors (422)
            let errorMessage = 'Unknown error';
            try {
                const errorData = await response.json();
                if (errorData && Array.isArray(errorData.detail)) {
                    errorMessage = errorData.detail
                        .map(e => (e.msg || e.message || JSON.stringify(e)))
                        .join('; ');
                } else if (typeof errorData.detail === 'string') {
                    errorMessage = errorData.detail;
                } else if (errorData.message) {
                    errorMessage = errorData.message;
                }
            } catch (_) {
                // ignore JSON parse errors
            }
            console.error('Server error:', response.status, errorMessage);
            throw new Error(`Server error: ${response.status} - ${errorMessage}`);
        }
        
    } catch (error) {
        if (CONFIG.DEBUG_MODE) console.error('Error submitting form:', error);
        
        let errorMessage = 'Submission failed. Please try again.';
        if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Unable to connect to server. Please check your internet connection and try again.';
        } else if (error.message.includes('Server error')) {
            errorMessage = error.message;
        } else if (error.message.includes('NetworkError')) {
            errorMessage = 'Network error. Please check your connection and try again.';
        }
        
        showNotification(errorMessage, 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'JEET JAAUNGA 😏';
        submitBtn.classList.remove('loading');
    }
}

// Success Message
function showSuccessMessage() {
    formContainer.style.display = 'none';
    successMessage.style.display = 'block';
    
    // Add some celebration animation
    setTimeout(() => {
        successMessage.style.transform = 'scale(1.05)';
        setTimeout(() => {
            successMessage.style.transform = 'scale(1)';
        }, 200);
    }, 100);
}

// Notification System
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Remove after configured duration
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, CONFIG.NOTIFICATION_DURATION);
}


// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Enhanced input validation with debouncing
const debouncedValidateName = debounce(validateName, 300);
const debouncedValidateEmail = debounce(validateEmail, 300);
const debouncedValidateAnswer = debounce(validateAnswer, 300);

nameInput.addEventListener('input', debouncedValidateName);
emailInput.addEventListener('input', debouncedValidateEmail);
answerInput.addEventListener('input', debouncedValidateAnswer);

// Keyboard accessibility
document.addEventListener('keydown', function(e) {
    // Close modal with Escape key
    if (e.key === 'Escape' && privacyModal.classList.contains('show')) {
        // Don't allow closing with Escape - user must make a choice
    }
    
    // Submit form with Enter key
    if (e.key === 'Enter' && !submitBtn.disabled && termsAccepted) {
        if (document.activeElement === nameInput || document.activeElement === emailInput || document.activeElement === answerInput) {
            contestForm.dispatchEvent(new Event('submit'));
        }
    }
});

// This handler is now handled in handleFormSubmit function

// Add loading state to submit button
function setLoadingState(isLoading) {
    if (isLoading) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> Submitting...';
    } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'JEET JAAUNGA 😏';
    }
}

// Add loading spinner CSS
const loadingStyle = document.createElement('style');
loadingStyle.textContent = `
    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid rgba(0, 0, 0, 0.3);
        border-radius: 50%;
        border-top-color: #000000;
        animation: spin 1s ease-in-out infinite;
        margin-right: 8px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
`;
document.head.appendChild(loadingStyle);

// Initialize form state
function initializeForm() {
    if (termsAccepted) {
        enableForm();
    } else {
        disableForm();
    }
}

// Call initialization
initializeForm();

// Add a test function for debugging (only available in debug mode)
if (CONFIG.DEBUG_MODE) {
    window.testAccept = function() {
        console.log('Manual test: accepting terms');
        acceptTerms();
    };

    window.testShowForm = function() {
        console.log('Manual test: showing form');
        termsAccepted = true;
        showForm();
    };

    window.checkState = function() {
        console.log('Current state:');
        console.log('- termsAccepted:', termsAccepted);
        console.log('- formContainer classes:', formContainer.className);
        console.log('- declineMessage display:', declineMessage.style.display);
        console.log('- form inputs disabled:', nameInput.disabled, emailInput.disabled, answerInput.disabled);
        console.log('- submit button disabled:', submitBtn.disabled);
    };
}

window.testBackend = async function() {
    try {
        console.log('Testing backend connection...');
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            console.log('Backend is running:', data);
            return true;
        } else {
            console.error('Backend responded with error:', response.status);
            return false;
        }
    } catch (error) {
        console.error('Backend is not running or not accessible:', error);
        console.log('Make sure to run: uvicorn backend.main:app --reload');
        return false;
    }
};

