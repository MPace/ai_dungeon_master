/**
 * Game Interface Module with Memory Integration
 * 
 * This module handles the interaction between the player and the AI Dungeon Master
 * on the game page. It manages the chat interface, character sheet, dice rolling,
 * and integrates with the memory system.
 */

// Session data
let sessionId = null;
let gameState = 'intro';

// Character reference
const character = characterData; // From global variable set in the HTML

/**
 * Initialize the game interface
 */
function initGameInterface() {
    console.log('Initializing game interface...');
    
    // Ensure character data exists
    if (typeof characterData === 'undefined') {
        console.error('Character data is undefined!');
        return;
    }
    
    console.log('Character data loaded:', characterData);
    
    // Add character reference for compatibility
    window.character = characterData;
    
    // Log character properties
    console.log('Character name:', characterData.name);
    console.log('Character abilities:', characterData.abilities);
    
    try {
        // Update character sheet
        updateCharacterSheet();
        
        // Set up event listeners
        setupChatEvents();
        setupDiceEvents();
        setupLogControls();
        setupMessageContextMenu();
        
        // Check if we're resuming a previous session
        checkForExistingSession();
        
        // Ensure chat window is scrolled to bottom initially
        scrollChatToBottom();
        
        // Handle window resize for mobile adjustments
        window.addEventListener('resize', handleResize);
        handleResize();
        
        console.log('Game interface initialized successfully');
    } catch (error) {
        console.error('Error during game interface initialization:', error);
    }
}

/**
 * Handle window resize events for responsive adjustments
 */
function handleResize() {
    const chatWindow = document.getElementById('chatWindow');
    const sidebar = document.querySelector('.sidebar-column');
    const diceRoller = document.querySelector('.dice-roller-container');
    
    // Keep dice roller on the right side regardless of screen size
    // Just adjust its position slightly for very small screens
    diceRoller.style.right = '20px';
    diceRoller.style.left = 'auto';
    
    if (window.innerWidth < 400) {
        diceRoller.style.bottom = '80px'; // Move up a bit on very small screens to avoid overlap with input
    } else {
        diceRoller.style.bottom = '20px';
    }
    
    // Ensure chat is scrolled to bottom on resize
    scrollChatToBottom();
}

/**
 * Update the character sheet sidebar with character data
 */
function updateCharacterSheet() {
    const characterSheet = document.getElementById('characterSheet');
    
    if (!characterSheet) return;
    
    let html = `
        <div class="character-header mb-3">
            <h4 class="text-center">${character.name}</h4>
            <p class="text-center text-light">Level ${character.level} ${capitalize(character.race)} ${capitalize(character.class)}</p>
        </div>
    `;
    
    // Add ability scores
    html += '<div class="ability-scores mb-3"><div class="row">';
    
    Object.entries(character.abilities).forEach(([ability, score]) => {
        const modifier = Math.floor((score - 10) / 2);
        const modText = modifier >= 0 ? `+${modifier}` : modifier;
        
        // Use standard D&D ability abbreviations
        let abilityAbbrev;
        switch(ability) {
            case 'strength': abilityAbbrev = 'STR'; break;
            case 'dexterity': abilityAbbrev = 'DEX'; break;
            case 'constitution': abilityAbbrev = 'CON'; break;
            case 'intelligence': abilityAbbrev = 'INT'; break;
            case 'wisdom': abilityAbbrev = 'WIS'; break;
            case 'charisma': abilityAbbrev = 'CHA'; break;
            default: abilityAbbrev = ability.substr(0, 3).toUpperCase();
        }
        
        html += `
            <div class="col-4 mb-2">
                <div class="ability-score">
                    <div class="ability-name">${abilityAbbrev}</div>
                    <div class="ability-value">${score}</div>
                    <div class="ability-modifier">${modText}</div>
                </div>
            </div>
        `;
    });
    
    html += '</div></div>';
    
    // Add hit points display
    if (character.hitPoints) {
        html += `
            <div class="hit-points-display mb-3">
                <div class="hp-header d-flex justify-content-between align-items-center">
                    <span>Hit Points</span>
                    <span class="hit-die-small">d${character.hitPoints.hitDie?.substring(1) || '8'}</span>
                </div>
                <div class="hp-bar">
                    <div class="current-hp">${character.hitPoints.current}/${character.hitPoints.max}</div>
                </div>
            </div>
        `;
    }
    
    // Add skills
    if (character.skills && character.skills.length > 0) {
        html += `
            <h5>Skills</h5>
            <div class="mb-3">
        `;
        
        character.skills.forEach(skill => {
            html += `<span class="badge bg-success me-1 mb-1">${capitalize(skill)}</span> `;
        });
        
        html += `
            </div>
        `;
    }
    
    // Add class features (simplified)
    if (character.features) {
        html += `<h5>Features</h5><div class="mb-3 small">`;
        
        // Required features
        if (character.features.required && character.features.required.length > 0) {
            character.features.required.forEach(feature => {
                html += `<div>${capitalize(feature)}</div>`;
            });
        }
        
        // Optional features
        if (character.features.optional) {
            Object.entries(character.features.optional).forEach(([featureType, value]) => {
                if (Array.isArray(value)) {
                    // For features with multiple selections (e.g. expertise skills)
                    html += `<div>${capitalize(featureType)}: ${value.map(capitalize).join(', ')}</div>`;
                } else {
                    // For single selection features
                    html += `<div>${capitalize(value)} ${featureType}</div>`;
                }
            });
        }
        
        html += `</div>`;
    }
    
    // Add equipment (simplified)
    if (character.equipment) {
        html += `<h5>Equipment</h5><div class="mb-3 small">`;
        
        // Selected equipment
        if (character.equipment.selected && character.equipment.selected.length > 0) {
            character.equipment.selected.forEach(item => {
                html += `<div>${item.name}</div>`;
            });
        }
        
        // Standard equipment (first few items to save space)
        if (character.equipment.standard && character.equipment.standard.length > 0) {
            const displayItems = character.equipment.standard.slice(0, 5);
            displayItems.forEach(item => {
                html += `<div>${item.name}</div>`;
            });
            
            if (character.equipment.standard.length > 5) {
                html += `<div>+${character.equipment.standard.length - 5} more items</div>`;
            }
        }
        
        html += `</div>`;
    }
    
    // Add spellcasting info if relevant
    if (character.spellcasting) {
        html += addSpellcastingToSheet();
    }
    
    characterSheet.innerHTML = html;
}

/**
 * Generate HTML for spellcasting section of character sheet
 * @returns {string} HTML for spellcasting section
 */
function addSpellcastingToSheet() {
    let html = `
        <h5>Spellcasting</h5>
        <div class="spellcasting-info small mb-3">
            <div><strong>Ability:</strong> ${capitalize(character.spellcasting.ability)}</div>
            <div><strong>Spell DC:</strong> ${character.spellcasting.spellSaveDC}</div>
            <div><strong>Attack:</strong> +${character.spellcasting.spellAttackBonus}</div>
        `;
    
    // Add cantrips and spells
    if (character.spellcasting.cantripsKnown && character.spellcasting.cantripsKnown.length > 0) {
        html += `<div class="mt-2"><strong>Cantrips:</strong> ${character.spellcasting.cantripsKnown.join(', ')}</div>`;
    }
    
    const preparedSpells = character.class === 'wizard' ? 
        character.spellcasting.spellsPrepared : 
        character.spellcasting.spellsKnown;
    
    if (preparedSpells && preparedSpells.length > 0) {
        html += `<div><strong>Spells:</strong> ${preparedSpells.join(', ')}</div>`;
    }
    
    // Add spell slots
    if (character.spellcasting.spellSlots) {
        html += `<div><strong>Slots:</strong> `;
        Object.entries(character.spellcasting.spellSlots).forEach(([level, slots]) => {
            html += `L${level}: ${slots} `;
        });
        html += `</div>`;
    }
    
    html += `</div>`;
    
    return html;
}

/**
 * Set up chat-related event listeners
 */
function setupChatEvents() {
    const playerInput = document.getElementById('playerInput');
    const sendButton = document.getElementById('sendButton');
    const chatWindow = document.getElementById('chatWindow');
    
    // Send button click
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    // Enter key in input field
    if (playerInput) {
        playerInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Focus on input field by default
        playerInput.focus();
    }
    
    // Function to send message
    window.sendMessage = function() {
        if (!playerInput) return;
        
        const message = playerInput.value.trim();
        if (!message) return;
        
        // Add player message to chat
        addMessageToChat(message, 'player');
        
        // Clear input field
        playerInput.value = '';
        
        // Focus back on input field for next message
        playerInput.focus();
        
        // Send to server
        sendToServer(message);
    };
    
    // Assign to window for external access
    if (typeof window !== 'undefined') {
        window.sendMessage = sendMessage;
    }
}

/**
 * Set up context menu for messages
 */
function setupMessageContextMenu() {
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) return;
    
    // Add context menu event listener
    chatWindow.addEventListener('contextmenu', function(e) {
        // Find closest message element
        const messageEl = e.target.closest('.message');
        if (messageEl) {
            e.preventDefault();
            showMessageContextMenu(e, messageEl);
        }
    });
}

/**
 * Show context menu for message
 * @param {MouseEvent} e - Mouse event
 * @param {HTMLElement} messageEl - Message element
 */
function showMessageContextMenu(e, messageEl) {
    // Remove any existing context menu
    const existingMenu = document.getElementById('messageContextMenu');
    if (existingMenu) {
        existingMenu.remove();
    }
    
    // Get message text
    const messageText = messageEl.textContent.trim();
    const isPlayerMessage = messageEl.classList.contains('player-message');
    
    // Create context menu
    const contextMenu = document.createElement('div');
    contextMenu.id = 'messageContextMenu';
    contextMenu.className = 'bg-dark text-light border border-secondary rounded shadow-lg p-2';
    contextMenu.style.position = 'fixed';
    contextMenu.style.zIndex = '1000';
    contextMenu.style.top = `${e.clientY}px`;
    contextMenu.style.left = `${e.clientX}px`;
    contextMenu.style.minWidth = '200px';
    
    // Menu items
    contextMenu.innerHTML = `
        <div class="context-item p-2 d-flex align-items-center" data-action="pin">
            <i class="bi bi-pin-angle me-2"></i>Pin to Memory
        </div>
        <div class="context-item p-2 d-flex align-items-center" data-action="copy">
            <i class="bi bi-clipboard me-2"></i>Copy Text
        </div>
    `;
    
    // Add click handlers
    contextMenu.querySelectorAll('.context-item').forEach(item => {
        item.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            
            if (action === 'pin') {
                pinMessageAsMemory(messageText, isPlayerMessage ? 'player' : 'dm');
            } else if (action === 'copy') {
                navigator.clipboard.writeText(messageText).then(() => {
                    showToast('Text copied to clipboard', 'success');
                }).catch(err => {
                    console.error('Error copying text:', err);
                    showToast('Failed to copy text', 'error');
                });
            }
            
            contextMenu.remove();
        });
        
        // Add hover effect
        item.addEventListener('mouseenter', function() {
            this.classList.add('bg-primary');
        });
        
        item.addEventListener('mouseleave', function() {
            this.classList.remove('bg-primary');
        });
    });
    
    // Add to document
    document.body.appendChild(contextMenu);
    
    // Click outside to close
    document.addEventListener('click', function closeMenu(e) {
        if (!contextMenu.contains(e.target)) {
            contextMenu.remove();
            document.removeEventListener('click', closeMenu);
        }
    });
}

/**
 * Pin a message as a memory
 * @param {string} content - Message content
 * @param {string} sender - Message sender (player/dm)
 */
function pinMessageAsMemory(content, sender) {
    if (!sessionId) {
        alert('No active session found. Please start a conversation first.');
        return;
    }
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Create and store a new memory
    fetch(`/api/memories/${sessionId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            content: content,
            memory_type: 'long_term',
            importance: 8, // Higher importance for manually pinned memories
            metadata: {
                sender: sender,
                pinned: true,
                pinned_at: new Date().toISOString()
            }
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Show success message
            showToast('Message pinned to memory', 'success');
            
            // Notify memory management system
            if (typeof refreshMemories === 'function') {
                refreshMemories();
            }
        } else {
            console.error('Error pinning message:', data.error);
            showToast(`Error pinning message: ${data.error || 'Unknown error'}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error pinning message:', error);
        showToast(`Error pinning message: ${error.message}`, 'error');
    });
}

/**
 * Show a toast notification
 * @param {string} message - Toast message
 * @param {string} type - Toast type (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Remove existing toast container if any
    const existingContainer = document.getElementById('toastContainer');
    if (existingContainer) {
        existingContainer.remove();
    }
    
    // Create container
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1070';
    
    // Create toast
    container.innerHTML = `
        <div class="toast bg-dark text-light" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type === 'error' ? 'danger' : type} text-light">
                <strong class="me-auto">Game System</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(container);
    
    // Initialize and show Bootstrap toast
    const toastEl = container.querySelector('.toast');
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}

/**
 * Add a message to the chat window
 * @param {string} message - The message text
 * @param {string} sender - 'player' or 'dm'
 */
function addMessageToChat(message, sender) {
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    
    if (sender === 'player') {
        messageDiv.classList.add('player-message');
    } else {
        messageDiv.classList.add('dm-message');
    }
    
    const messagePara = document.createElement('p');
    messagePara.textContent = message;
    messageDiv.appendChild(messagePara);
    
    chatWindow.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollChatToBottom();
}

/**
 * Scroll the chat window to the bottom
 */
function scrollChatToBottom() {
    const chatWindow = document.getElementById('chatWindow');
    if (chatWindow) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}

/**
 * Send a message to the server
 * @param {string} message - The message to send
 */
function sendToServer(message) {
    console.log('Sending message to server:', message);
    
    // Show typing indicator
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) {
        console.error('Chat window element not found');
        return;
    }
    
    const typingDiv = document.createElement('div');
    typingDiv.classList.add('message', 'dm-message', 'typing-indicator');
    typingDiv.innerHTML = '<p>The DM is crafting a response...</p>';
    chatWindow.appendChild(typingDiv);
    
    // Scroll to show typing indicator
    scrollChatToBottom();
    
    // Use the global character variable
    const character = window.character || window.characterData;
    
    if (!character) {
        console.error('No character data available');
        chatWindow.removeChild(typingDiv);
        addMessageToChat('Error: Character data not available. Please refresh the page.', 'dm');
        return;
    }
    
    // Prepare data to send
    const data = {
        message: message,
        session_id: sessionId,
        character_data: character
    };
    
    console.log("Sending data:", {
        message_length: message.length,
        session_id: sessionId,
        character_id: character.character_id
    });
    
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (!csrfToken) {
        console.error('CSRF token not found');
        chatWindow.removeChild(typingDiv);
        addMessageToChat('Error: Security token missing. Please refresh the page.', 'dm');
        return;
    }
    
    // Send API request
    fetch('/game/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log('Response received:', response.status);
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Received response data:', data);
        
        // Remove typing indicator
        try {
            chatWindow.removeChild(typingDiv);
        } catch (e) {
            console.warn('Could not remove typing indicator:', e);
        }
        
        // Add response to chat
        addMessageToChat(data.response, 'dm');
        
        // Update session ID if provided
        if (data.session_id) {
            sessionId = data.session_id;
            saveSessionId(sessionId);
            console.log('Session ID updated:', sessionId);
            
            // Set session ID on chat window
            chatWindow.setAttribute('data-session-id', sessionId);
        }
        
        // Update game state if provided
        if (data.game_state) {
            gameState = data.game_state;
            console.log('Game state updated:', gameState);
            
            // Update UI based on game state
            updateUIForGameState(gameState);
        }
        
        // Handle newly detected entities
        if (data.entities_found && data.entities_found.length > 0) {
            handleNewEntities(data.entities_found);
        }
        
        // Dispatch event for other components to know about the response
        document.dispatchEvent(new CustomEvent('dm-response-received', { 
            detail: { 
                session_id: sessionId,
                game_state: gameState,
                entities: data.entities_found || []
            }
        }));
    })
    .catch(error => {
        console.error('Error communicating with server:', error);
        
        // Remove typing indicator
        try {
            chatWindow.removeChild(typingDiv);
        } catch (e) {
            console.warn('Could not remove typing indicator:', e);
        }
        
        // Add error message
        addMessageToChat(
            `The connection to the Dungeon Master seems unstable. Please try again. (Error: ${error.message})`,
            'dm'
        );
    });
}

/**
 * Handle newly detected entities
 * @param {Array} entities - New entities detected
 */
function handleNewEntities(entities) {
    if (!entities || entities.length === 0) return;
    
    // Show notification for important entities
    const importantEntities = entities.filter(entity => (entity.importance || 5) >= 8);
    
    if (importantEntities.length > 0) {
        const entityNames = importantEntities.map(entity => entity.name).join(', ');
        showToast(`Important entities detected: ${entityNames}`, 'info');
    }
}

/**
 * Set up dice roller event listeners
 */
function setupDiceEvents() {
    const diceButtons = document.querySelectorAll('[data-dice]');
    
    diceButtons.forEach(button => {
        button.addEventListener('click', function() {
            const diceType = this.getAttribute('data-dice');
            rollDice(diceType);
        });
    });
}

/**
 * Roll a die and add the result to the chat
 * @param {string} diceType - The type of die to roll (e.g., 'd20')
 */
function rollDice(diceType) {
    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Send API request
    fetch('/game/api/roll-dice', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            dice: diceType,
            modifier: 0
        })
    })
    .then(response => response.json())
    .then(data => {
        // Add dice roll result to chat
        const message = `🎲 Rolled ${diceType}: ${data.result}`;
        addMessageToChat(message, 'dm');
    })
    .catch(error => {
        console.error('Error rolling dice:', error);
        
        // Fallback to client-side dice roll if API fails
        const sides = parseInt(diceType.substring(1));
        const result = Math.floor(Math.random() * sides) + 1;
        
        const message = `🎲 Rolled ${diceType}: ${result} (client-side roll)`;
        addMessageToChat(message, 'dm');
    });
}

/**
 * Set up adventure log control buttons
 */
function setupLogControls() {
    const saveLogButton = document.getElementById('saveLogButton');
    const clearLogButton = document.getElementById('clearLogButton');
    
    if (saveLogButton) {
        saveLogButton.addEventListener('click', saveAdventureLog);
    }
    
    if (clearLogButton) {
        clearLogButton.addEventListener('click', clearAdventureLog);
    }
}

/**
 * Save the adventure log as a text file
 */
function saveAdventureLog() {
    const chatWindow = document.getElementById('chatWindow');
    if (!chatWindow) return;
    
    // Get all messages
    const messages = chatWindow.querySelectorAll('.message');
    
    // Create log content
    let logContent = `Adventure Log - ${character.name} - ${new Date().toLocaleString()}\n\n`;
    
    messages.forEach(message => {
        const sender = message.classList.contains('player-message') ? character.name : 'DM';
        const text = message.textContent.trim();
        
        logContent += `${sender}: ${text}\n\n`;
    });
    
    // Create blob and download
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `adventure_log_${character.name}_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    
    // Cleanup
    URL.revokeObjectURL(url);
}

/**
 * Clear the adventure log (with confirmation)
 */
function clearAdventureLog() {
    if (confirm('Are you sure you want to clear the adventure log? This cannot be undone.')) {
        const chatWindow = document.getElementById('chatWindow');
        if (!chatWindow) return;
        
        // Remove all messages except welcome message
        const messages = chatWindow.querySelectorAll('.message');
        
        // Keep the first message (welcome)
        for (let i = 1; i < messages.length; i++) {
            chatWindow.removeChild(messages[i]);
        }
        
        // Add a system message
        addMessageToChat('The adventure log has been cleared.', 'dm');
    }
}

/**
 * Update UI based on game state
 * @param {string} state - The current game state
 */
function updateUIForGameState(state) {
    // Get the adventure log card header
    const adventureLogHeader = document.querySelector('.card-header');
    if (!adventureLogHeader) return;
    
    // Reset classes
    adventureLogHeader.classList.remove('bg-danger', 'bg-info', 'bg-success');
    
    // Update based on state
    switch (state) {
        case 'combat':
            adventureLogHeader.classList.add('bg-danger');
            break;
        case 'exploration':
            adventureLogHeader.classList.add('bg-info');
            break;
        case 'social':
            adventureLogHeader.classList.add('bg-success');
            break;
        default:
            // Keep default styling
            break;
    }
}

/**
 * Check for an existing game session to resume
 */
function checkForExistingSession() {
    // Try to get saved session ID
    const savedSessionId = localStorage.getItem(`session_${character.character_id}`);
    
    if (savedSessionId) {
        sessionId = savedSessionId;
        console.log('Resuming previous session:', sessionId);
        
        // Set session ID on chat window
        const chatWindow = document.getElementById('chatWindow');
        if (chatWindow) {
            chatWindow.setAttribute('data-session-id', sessionId);
        }
        
        // Optionally: fetch previous messages from the server to populate chat history
    } else {
        // Start a new session with an introduction message
        sendInitialMessage();
    }
}

/**
 * Send initial message to start a new session
 */
function sendInitialMessage() {
    // Create an introduction for the AI
    const intro = `I am ${character.name}, a level ${character.level} ${character.race} ${character.class}. This is the start of our adventure. Please introduce the campaign setting and my first scene.`;
    
    // Add a log to help debug the message
    console.log("Sending initial message:", intro);
    
    // Send to server
    sendToServer(intro);
}

/**
 * Save session ID to localStorage
 * @param {string} id - Session ID to save
 */
function saveSessionId(id) {
    localStorage.setItem(`session_${character.character_id}`, id);
}

/**
 * Utility function to capitalize a string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

// Make functions available globally
window.gameInterface = {
    sendMessage,
    addMessageToChat,
    rollDice,
    saveAdventureLog,
    clearAdventureLog,
    pinMessageAsMemory,
    showToast
};

// Ensure DOM ready event is properly registered and initialize
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM content loaded, initializing game interface');
    
    // Initialize with a slight delay to ensure everything is loaded
    setTimeout(initGameInterface, 100);
});

// Add a global retry function for manual invocation if needed
window.retryInitialization = function() {
    console.log('Manually retrying initialization...');
    initGameInterface();
};