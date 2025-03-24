/**
 * Debug utilities for AI Dungeon Master
 * Add this script before the game-interface.js in dm.html
 */

// Add enhanced console logging
if (typeof console !== 'undefined') {
    // Save original methods
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    
    // Override console.log
    console.log = function() {
        // Get current timestamp
        const timestamp = new Date().toISOString().slice(11, 23);
        
        // Call original with timestamp prefix
        originalLog.apply(console, [`[${timestamp}]`, ...arguments]);
        
        // Optionally save logs for debugging
        if (!window.debugLogs) window.debugLogs = [];
        window.debugLogs.push({
            type: 'log',
            timestamp: new Date(),
            args: Array.from(arguments)
        });
    };
    
    // Override console.error
    console.error = function() {
        // Get current timestamp
        const timestamp = new Date().toISOString().slice(11, 23);
        
        // Call original with timestamp prefix
        originalError.apply(console, [`[${timestamp}] ERROR:`, ...arguments]);
        
        // Optionally save logs for debugging
        if (!window.debugLogs) window.debugLogs = [];
        window.debugLogs.push({
            type: 'error',
            timestamp: new Date(),
            args: Array.from(arguments)
        });
    };
    
    // Override console.warn
    console.warn = function() {
        // Get current timestamp
        const timestamp = new Date().toISOString().slice(11, 23);
        
        // Call original with timestamp prefix
        originalWarn.apply(console, [`[${timestamp}] WARNING:`, ...arguments]);
        
        // Optionally save logs for debugging
        if (!window.debugLogs) window.debugLogs = [];
        window.debugLogs.push({
            type: 'warn',
            timestamp: new Date(),
            args: Array.from(arguments)
        });
    };
}

// Add global error handler
window.addEventListener('error', function(event) {
    console.error('Uncaught error:', event.error);
    
    // Display error on page for debugging
    const errorDiv = document.createElement('div');
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '10px';
    errorDiv.style.left = '10px';
    errorDiv.style.backgroundColor = 'rgba(255, 0, 0, 0.8)';
    errorDiv.style.color = 'white';
    errorDiv.style.padding = '10px';
    errorDiv.style.borderRadius = '5px';
    errorDiv.style.zIndex = '9999';
    errorDiv.style.maxWidth = '80%';
    errorDiv.style.wordBreak = 'break-word';
    
    errorDiv.innerHTML = `
        <strong>JavaScript Error:</strong><br>
        ${event.message}<br>
        <small>${event.filename}:${event.lineno}:${event.colno}</small>
        <button style="display:block;margin-top:5px;padding:2px 5px;background:white;color:black;border:none;border-radius:3px;">Dismiss</button>
    `;
    
    // Add dismiss button handler
    errorDiv.querySelector('button').addEventListener('click', function() {
        document.body.removeChild(errorDiv);
    });
    
    document.body.appendChild(errorDiv);
});

// Function to check character data structure
function checkCharacterData() {
    console.log('Checking character data...');
    
    if (typeof characterData === 'undefined') {
        console.error('Character data is undefined!');
        return false;
    }
    
    console.log('Character data:', characterData);
    
    const requiredProps = ['name', 'race', 'class', 'level', 'abilities', 'character_id'];
    const missingProps = requiredProps.filter(prop => !characterData.hasOwnProperty(prop));
    
    if (missingProps.length > 0) {
        console.error('Missing required properties:', missingProps);
        return false;
    }
    
    // Check abilities structure
    if (!characterData.abilities || typeof characterData.abilities !== 'object') {
        console.error('Abilities is missing or not an object');
        return false;
    }
    
    const requiredAbilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
    const missingAbilities = requiredAbilities.filter(ability => !characterData.abilities.hasOwnProperty(ability));
    
    if (missingAbilities.length > 0) {
        console.warn('Some abilities missing:', missingAbilities);
    }
    
    return true;
}

// Run checks after page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Debug script loaded and running checks...');
    
    // Check character data
    setTimeout(checkCharacterData, 500);
    
    // Check if initialization happened
    setTimeout(function() {
        const characterSheet = document.getElementById('characterSheet');
        if (characterSheet && characterSheet.innerHTML.trim() === '') {
            console.error('Character sheet is empty after loading!');
            
            // Try to manually initialize
            console.log('Attempting manual initialization...');
            if (typeof initGameInterface === 'function') {
                initGameInterface();
            } else {
                console.error('initGameInterface function not found');
            }
        }
    }, 1000);
});