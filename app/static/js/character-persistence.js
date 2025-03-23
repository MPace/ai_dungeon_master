/**
 * Character Persistence Module
 * 
 * This module handles saving and loading character data during the creation process,
 * both to the server and locally for state management. It's designed to work with
 * the multi-page architecture and browser navigation.
 */

// Auto-save configuration
const AUTOSAVE_INTERVAL = 30000; // 30 seconds
let autosaveTimer = null;

// Last saved timestamp
let lastSavedTimestamp = 0;

/**
 * Initialize state tracking
 * Sets up autosave and browser navigation handling
 */
function initStateTracking() {
    console.log('Initializing character state tracking');
    
    // Start autosave timer
    startAutosave();
    
    // Check URL for step parameter
    const urlParams = new URLSearchParams(window.location.search);
    const stepParam = urlParams.get('step');
    
    // If step is in URL but not in history state, add it
    if (stepParam && (!window.history.state || window.history.state.step !== parseInt(stepParam))) {
        window.history.replaceState({ step: parseInt(stepParam) }, '', window.location.href);
    }
    
    // Set up beforeunload handler to warn about unsaved changes
    window.onbeforeunload = handlePageUnload;
    
    return true;
}

/**
 * Handle page unload event
 * @param {BeforeUnloadEvent} event - The beforeunload event
 */
function handlePageUnload(event) {
    // Only show warning if unsaved changes exist and we're not in the submission process
    if (Date.now() - lastSavedTimestamp > 5000 && !window.isSubmittingCharacter) {
        const message = 'You have unsaved character changes. Are you sure you want to leave?';
        event.returnValue = message;
        return message;
    }
}

/**
 * Start the autosave timer
 */
function startAutosave() {
    if (autosaveTimer) {
        clearInterval(autosaveTimer);
    }
    
    autosaveTimer = setInterval(() => {
        // Get the current character data from the main module
        // This requires the character-creation.js module to expose characterData
        // Use a try-catch in case it's not available
        try {
            const characterModule = window.characterCreation;
            if (characterModule && characterModule.characterData) {
                saveCharacterDraft(characterModule.characterData);
            }
        } catch (e) {
            console.warn('Could not access character data for autosave', e);
        }
    }, AUTOSAVE_INTERVAL);
    
    console.log('Autosave timer started');
}

/**
 * Stop the autosave timer
 */
function stopAutosave() {
    if (autosaveTimer) {
        clearInterval(autosaveTimer);
        autosaveTimer = null;
        console.log('Autosave timer stopped');
    }
}

/**
 * Save character progress
 * @param {Object} characterData - The character data to save
 * @param {number} currentStep - The current creation step
 */
function saveProgress(characterData, currentStep) {
    // Mark as draft
    characterData.isDraft = true;
    characterData.lastStep = currentStep;
    
    // Save locally for immediate access
    saveLocalProgress(characterData);
    
    // Save to server
    saveCharacterDraft(characterData);
}

/**
 * Save character progress locally (session storage)
 * @param {Object} characterData - The character data to save
 */
function saveLocalProgress(characterData) {
    try {
        // Create a clean copy to avoid circular references
        const characterCopy = JSON.parse(JSON.stringify(characterData));
        
        // Save to session storage (will be cleared when browser is closed)
        sessionStorage.setItem('character_draft', JSON.stringify(characterCopy));
        
        // Update last saved timestamp
        lastSavedTimestamp = Date.now();
        
        console.log('Character saved locally');
    } catch (e) {
        console.error('Error saving character data locally', e);
    }
}

/**
 * Load character progress from local storage
 * @returns {Object|null} The character data or null if not found
 */
function loadLocalProgress() {
    try {
        const characterJson = sessionStorage.getItem('character_draft');
        if (characterJson) {
            return JSON.parse(characterJson);
        }
    } catch (e) {
        console.error('Error loading character data from local storage', e);
    }
    return null;
}

/**
 * Save character draft to server
 * @param {Object} characterData - The character data to save
 * @returns {Promise} Promise that resolves when save is complete
 */
function saveCharacterDraft(characterData) {
    // Don't save empty drafts
    if (!characterData || !characterData.name) {
        return Promise.resolve(null);
    }
    
    return new Promise((resolve, reject) => {
        // Show saving indicator
        showSavingIndicator();

        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
        
        // Send API request
        fetch('/characters/api/save-character-draft', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(characterData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Server returned ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log('Character draft saved to server');
                
                // Update the character ID if provided
                if (data.character_id) {
                    characterData.character_id = data.character_id;
                }
                
                // Update last saved timestamp
                lastSavedTimestamp = Date.now();
                
                // Show success indicator
                showSaveSuccessIndicator();
                
                resolve(data);
            } else {
                console.error('Error saving character draft:', data.error);
                reject(new Error(data.error || 'Failed to save character draft'));
            }
        })
        .catch(error => {
            console.error('Network error saving character draft:', error);
            
            // Show error indicator
            showSaveErrorIndicator();
            
            reject(error);
        });
    });
}

/**
 * Complete the character creation process
 * @param {Object} characterData - The finalized character data
 * @returns {Promise} Promise that resolves with the saved character
 */

function completeCharacter(characterData) {
    // Mark as completed
    characterData.isDraft = false;
    characterData.completedAt = new Date().toISOString();
    
    // Set a flag to indicate we're in submission process
    window.isSubmittingCharacter = true;
    
    // Remove the beforeunload warning
    window.onbeforeunload = null;
    
    // Clean up draft data
    cleanupDraftData();
    
    // Stop autosave
    stopAutosave();
    
    return Promise.resolve({
        ...characterData,
        character_id: characterData.character_id
    });
}

/**
 * Clean up draft data after character creation is complete
 * Also cleans up event handlers to prevent navigation warnings
 */
function cleanupDraftData() {
    // Remove the beforeunload handler to prevent navigation warning
    window.onbeforeunload = null;
    
    // Set a flag to indicate we're in submission process
    window.isSubmittingCharacter = true;
    
    // Clear session storage
    sessionStorage.removeItem('character_draft');
    
    // Clear any other local storage used for drafts
    console.log('Draft data cleaned up');
}

/**
 * Complete the character creation process
 * @param {Object} characterData - The finalized character data
 * @returns {Promise} Promise that resolves with the saved character
 */

// UI Feedback Functions
function showSavingIndicator() {
    removeExistingIndicators();
    
    const indicator = document.createElement('div');
    indicator.className = 'save-indicator saving';
    indicator.textContent = 'Saving...';
    document.body.appendChild(indicator);
    
    // Auto-remove after 2 seconds
    setTimeout(() => {
        if (document.body.contains(indicator)) {
            document.body.removeChild(indicator);
        }
    }, 2000);
}

function showSaveSuccessIndicator() {
    removeExistingIndicators();
    
    const indicator = document.createElement('div');
    indicator.className = 'save-indicator success';
    indicator.textContent = 'Saved';
    document.body.appendChild(indicator);
    
    // Auto-remove after 2 seconds
    setTimeout(() => {
        if (document.body.contains(indicator)) {
            document.body.removeChild(indicator);
        }
    }, 2000);
}

function showSaveErrorIndicator() {
    removeExistingIndicators();
    
    const indicator = document.createElement('div');
    indicator.className = 'save-indicator error';
    indicator.textContent = 'Error saving';
    document.body.appendChild(indicator);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (document.body.contains(indicator)) {
            document.body.removeChild(indicator);
        }
    }, 3000);
}

function removeExistingIndicators() {
    const existingIndicators = document.querySelectorAll('.save-indicator');
    existingIndicators.forEach(indicator => {
        document.body.removeChild(indicator);
    });
}

// Add the CSS for the save indicators
function addSaveIndicatorStyles() {
    if (!document.getElementById('save-indicator-styles')) {
        const style = document.createElement('style');
        style.id = 'save-indicator-styles';
        style.textContent = `
            .save-indicator {
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                color: white;
                z-index: 9999;
                animation: fadeInOut 2s ease-in-out;
            }
            
            .save-indicator.saving {
                background-color: rgba(70, 70, 70, 0.9);
            }
            
            .save-indicator.success {
                background-color: rgba(40, 167, 69, 0.9);
            }
            
            .save-indicator.error {
                background-color: rgba(220, 53, 69, 0.9);
            }
            
            @keyframes fadeInOut {
                0% { opacity: 0; transform: translateY(10px); }
                20% { opacity: 1; transform: translateY(0); }
                80% { opacity: 1; transform: translateY(0); }
                100% { opacity: 0; transform: translateY(10px); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Add the styles when this module is imported
addSaveIndicatorStyles();

// Export functions for use in other modules
export {
    initStateTracking,
    saveProgress,
    loadLocalProgress,
    completeCharacter
};