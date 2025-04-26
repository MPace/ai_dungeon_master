// File: frontend/src/services/api.js

/**
 * API Service for the AI Dungeon Master application
 * Handles all API requests to the backend
 */

// Helper function to get CSRF token
const getCsrfToken = () => {
    const tokenMeta = document.querySelector('meta[name="csrf-token"]');
    return tokenMeta ? tokenMeta.getAttribute('content') : '';
};

// Helper for fetch requests with error handling
const fetchWithErrorHandling = async (url, options = {}) => {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            // Try to parse JSON error response
            try {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            } catch (jsonError) {
                throw new Error(`HTTP error ${response.status}`);
            }
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API Error (${url}):`, error);
        throw error;
    }
};

/**
 * Dashboard API functions - Updated to use dashboard blueprint
 */

// Get all characters for the current user
export const getCharacters = async () => {
    return fetchWithErrorHandling('/dashboard/api/characters');
};

// Get all character drafts for the current user
export const getDrafts = async () => {
    return fetchWithErrorHandling('/dashboard/api/character-drafts');
};

// Delete a character
export const deleteCharacter = async (characterId) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling(`/characters/api/delete-character/${characterId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ character_id: characterId })
    });
};

// Delete a character draft
export const deleteDraft = async (draftId) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling(`/characters/api/delete-draft/${draftId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ draft_id: draftId })
    });
};

/**
 * Character Creation API functions
 */

// Save a character (complete)
export const saveCharacter = async (characterData) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling('/characters/api/save-character', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(characterData)
    });
};

// Save a character draft
export const saveCharacterDraft = async (characterData) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling('/characters/api/save-character-draft', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(characterData)
    });
};

// Get a character by ID
export const getCharacter = async (characterId) => {
    return fetchWithErrorHandling(`/dashboard/api/character/${characterId}`);
};

// Get a character draft by ID
export const getCharacterDraft = async (draftId) => {
    return fetchWithErrorHandling(`/dashboard/api/character-draft/${draftId}`);
};

// Get worlds
export const getWorlds = async () => {
    return fetchWithErrorHandling('/characters/api/worlds');
};

// Get campaigns for a world
export const getCampaigns = async (worldId) => {
    return fetchWithErrorHandling(`/characters/api/campaigns/${worldId}`);
};

// Get creation data for a world (classes, races, etc.)
export const getCreationData = async (worldId) => {
    return fetchWithErrorHandling(`/characters/api/creation-data/${worldId}`);
};

// Get premade characters for a world
export const getPremadeCharacters = async (worldId) => {
    return fetchWithErrorHandling(`/characters/api/premade-characters/${worldId}`);
};

/**
 * Game API functions
 */

// Send a message to the DM
export const sendMessage = async (message, sessionId, characterData) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling('/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            message,
            session_id: sessionId,
            character_data: characterData
        })
    });
};

// Check the status of a task
export const checkTaskStatus = async (taskId) => {
    return fetchWithErrorHandling(`/api/check-task/${taskId}`);
};

// Roll dice
export const rollDice = async (diceType, modifier, sessionId) => {
    const csrfToken = getCsrfToken();
    
    return fetchWithErrorHandling('/api/roll-dice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            dice: diceType,
            modifier: modifier || 0,
            session_id: sessionId
        })
    });
};

export default {
    // Dashboard
    getCharacters,
    getDrafts,
    deleteCharacter,
    deleteDraft,
    
    // Character Creation
    saveCharacter,
    saveCharacterDraft,
    getCharacter,
    getCharacterDraft,
    getWorlds,
    getCampaigns,
    getCreationData,
    getPremadeCharacters,
    
    // Game
    sendMessage,
    checkTaskStatus,
    rollDice
};