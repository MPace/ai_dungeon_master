// Main JavaScript for the AI Dungeon Master

// Wait for the DOM to be fully loaded before attaching event listeners
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing AI DM interface');
    
    // DOM Elements
    const chatWindow = document.getElementById('chatWindow');
    const playerInput = document.getElementById('playerInput');
    const sendButton = document.getElementById('sendButton');
    const diceButtons = document.querySelectorAll('[data-dice]');
    
    // Check if elements were found
    console.log('Chat window found:', !!chatWindow);
    console.log('Player input found:', !!playerInput);
    console.log('Send button found:', !!sendButton);
    console.log('Number of dice buttons found:', diceButtons.length);
    
    // Event Listeners
    if (sendButton) {
        sendButton.onclick = function() {
            console.log('Send button clicked');
            sendMessage();
        };
    }
    
    if (playerInput) {
        playerInput.onkeypress = function(e) {
            if (e.key === 'Enter') {
                console.log('Enter key pressed in input');
                sendMessage();
            }
        };
    }
    
    // Add dice roll event listeners
    diceButtons.forEach(button => {
        button.onclick = function() {
            const diceType = this.getAttribute('data-dice');
            console.log('Dice button clicked:', diceType);
            rollDice(diceType);
        };
    });
    
    // Functions
    function sendMessage() {
        if (!playerInput) {
            console.error('Player input element not found');
            return;
        }
        
        const message = playerInput.value.trim();
        console.log('Attempting to send message:', message);
        
        if (message === '') {
            console.log('Message was empty, not sending');
            return;
        }
        
        // Add player message to chat
        addMessageToChat(message, 'player');
        
        // Clear input field
        playerInput.value = '';
        
        // Focus back on input field for next message
        playerInput.focus();
        
        // Send to backend and get response
        sendToBackend(message);
    }
    
    function addMessageToChat(message, sender) {
        if (!chatWindow) {
            console.error('Chat window element not found');
            return;
        }
        
        console.log('Adding message to chat. Sender:', sender, 'Message:', message);
        
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
        
        // Scroll to the latest message
        scrollToBottom();
    }
    
    function scrollToBottom() {
        if (!chatWindow) {
            console.error('Chat window element not found');
            return;
        }
        
        // Smooth scroll to the bottom of the chat window
        chatWindow.scrollTo({
            top: chatWindow.scrollHeight,
            behavior: 'smooth'
        });
    }
    
    function rollDice(diceType) {
        if (!diceType) {
            console.error('No dice type specified');
            return;
        }
        
        console.log('Rolling dice:', diceType);
        
        // Parse the dice type (e.g., "d20" -> 20)
        const sides = parseInt(diceType.substring(1));
        
        if (isNaN(sides) || sides <= 0) {
            console.error('Invalid dice type:', diceType);
            return;
        }
        
        // Generate a random number
        const result = Math.floor(Math.random() * sides) + 1;
        
        // Create a message for the result
        const message = `🎲 Rolled ${diceType}: ${result}`;
        console.log(message);
        
        // Add to chat
        addMessageToChat(message, 'dm');
    }
    
    // Global variables for session management
    let sessionId = null;
    let gameState = 'intro';
    
    function sendToBackend(message) {
        console.log('Sending message to backend:', message);
        
        // Show "typing" indicator
        const typingDiv = document.createElement('div');
        typingDiv.classList.add('message', 'dm-message', 'typing-indicator');
        typingDiv.innerHTML = '<p>The DM is crafting a response...</p>';
        chatWindow.appendChild(typingDiv);
        
        // Scroll to make typing indicator visible
        scrollToBottom();
        
        // Prepare the data to send
        const data = {
            message: message,
            session_id: sessionId
        };
        
        // Send the API request
        console.log('Sending fetch request to /api/send-message');
        fetch('/api/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received response:', data);
            
            // Remove typing indicator
            chatWindow.removeChild(typingDiv);
            
            // Add response to chat
            addMessageToChat(data.response, 'dm');
            
            // Update session ID if provided
            if (data.session_id) {
                sessionId = data.session_id;
                console.log('Session ID updated:', sessionId);
            }
            
            // Update game state if provided
            if (data.game_state) {
                gameState = data.game_state;
                console.log('Game state updated:', gameState);
                
                // Optionally update UI based on game state
                updateUIForGameState(gameState);
            }
        })
        .catch(error => {
            console.error('Fetch Error:', error);
            
            // Try to remove typing indicator (may fail if already removed)
            try {
                chatWindow.removeChild(typingDiv);
            } catch (e) {
                console.log('Could not remove typing indicator', e);
            }
            
            // Add detailed error message to chat
            const errorMessage = `API Error: ${error.message}. This could be due to CORS issues, network connectivity, or server not running properly.`;
            console.error(errorMessage);
            
            addMessageToChat(
                "The connection to the Dungeon Master seems unstable. Please try again. (Error: " + error.message + ")",
                'dm'
            );
        });
    }
    
    function updateUIForGameState(state) {
        // Optional: Update UI elements based on the current game state
        // For example, change background colors, show/hide elements, etc.
        
        // Get the adventure log card header
        const adventureLogHeader = document.querySelector('.card-header');
        
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
});