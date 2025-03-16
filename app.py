from flask import Flask, render_template, request, jsonify, session, send_from_directory
import os
import json
import random
from datetime import datetime
import uuid
from dotenv import load_dotenv
from xai_handler import XAIHandler

# Initialize Flask app
app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.secret_key = os.urandom(24)  # For session management

# Ensure directory structure exists
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Print debug information
print("=== Starting AI Dungeon Master ===")
print(f"Current working directory: {os.getcwd()}")

# Load environment variables
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")
load_dotenv()

# Initialize AI handler with API credentials
API_KEY = os.getenv('AI_API_KEY')
AI_MODEL = os.getenv('AI_MODEL', 'grok-1')  # Default to grok-1 if not specified

print(f"API_KEY found: {'Yes' if API_KEY else 'No'}")
if API_KEY:
    print(f"API_KEY starts with: {API_KEY[:8]}...")
print(f"Using model: {AI_MODEL}")

# Initialize the AI handler
try:
    print("Initializing XAIHandler...")
    ai_handler = XAIHandler(API_KEY, AI_MODEL)
    print(f"XAI handler initialized successfully with model: {AI_MODEL}")
except Exception as e:
    print(f"ERROR initializing XAIHandler: {e}")
    import traceback
    traceback.print_exc()
    ai_handler = None
    print("Falling back to mock responses due to initialization error.")

# In-memory database for sessions
SESSIONS_DB = {}

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html')

@app.route('/api-test')
def api_test():
    """Render the API test page"""
    return render_template('api_test.html')

@app.route('/test-api', methods=['GET'])
def test_api():
    """Simple endpoint to test if API is working"""
    return jsonify({
        'status': 'success',
        'message': 'API is working properly',
        'ai_handler_available': ai_handler is not None
    })

@app.route('/api/send-message', methods=['POST'])
def send_message():
    """Process a message from the player and return a DM response"""
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    print(f"\n--- New message received: '{message}' ---")
    
    # If no session ID or invalid, create a new session
    if not session_id or session_id not in SESSIONS_DB:
        session_id = str(uuid.uuid4())
        SESSIONS_DB[session_id] = {
            'history': [],
            'character': None,
            'game_state': 'intro'
        }
        print(f"Created new session: {session_id}")
    else:
        print(f"Using existing session: {session_id}")
    
    # Add player message to history
    SESSIONS_DB[session_id]['history'].append({
        'sender': 'player',
        'message': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Process the message and generate a response
    if ai_handler:
        print(f"Using AI handler with model: {AI_MODEL}")
        # Use AI handler to generate response
        response = ai_handler.generate_response(
            player_message=message,
            conversation_history=SESSIONS_DB[session_id]['history'],
            character_data=SESSIONS_DB[session_id]['character'],
            game_state=SESSIONS_DB[session_id]['game_state']
        )
        print(f"AI response generated: '{response[:50]}...'")
        
        # Update game state based on message content (simplified)
        old_state = SESSIONS_DB[session_id]['game_state']
        if any(word in message.lower() for word in ['attack', 'fight', 'hit', 'cast']):
            SESSIONS_DB[session_id]['game_state'] = 'combat'
        elif any(word in message.lower() for word in ['talk', 'speak', 'ask', 'say']):
            SESSIONS_DB[session_id]['game_state'] = 'social'
        elif any(word in message.lower() for word in ['look', 'search', 'investigate', 'explore']):
            SESSIONS_DB[session_id]['game_state'] = 'exploration'
        
        if old_state != SESSIONS_DB[session_id]['game_state']:
            print(f"Game state changed from {old_state} to {SESSIONS_DB[session_id]['game_state']}")
    else:
        print("AI handler not available, using fallback response generator")
        # Fall back to rule-based responses if AI is not available
        response = generate_dm_response(message, SESSIONS_DB[session_id])
    
    # Add DM response to history
    SESSIONS_DB[session_id]['history'].append({
        'sender': 'dm',
        'message': response,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"Response sent to client with game state: {SESSIONS_DB[session_id]['game_state']}")
    
    return jsonify({
        'response': response,
        'session_id': session_id,
        'game_state': SESSIONS_DB[session_id]['game_state']
    })

@app.route('/api/roll-dice', methods=['POST'])
def roll_dice():
    """Handle dice rolling requests"""
    data = request.json
    dice_type = data.get('dice', 'd20')
    modifier = data.get('modifier', 0)
    
    # Parse the dice type (e.g., "d20" -> 20)
    sides = int(dice_type[1:])
    
    # Roll the dice
    result = random.randint(1, sides)
    modified_result = result + modifier
    
    return jsonify({
        'dice': dice_type,
        'result': result,
        'modifier': modifier,
        'modified_result': modified_result
    })

def generate_dm_response(message, session):
    """
    Generate a DM response based on the player's message and session state
    This is a fallback function used when the AI is not available
    """
    message_lower = message.lower()
    game_state = session.get('game_state', 'intro')
    
    print("WARNING: Using fallback response generator instead of AI!")
    
    # Very simple rule-based response for demonstration
    if game_state == 'intro':
        if any(word in message_lower for word in ['start', 'begin', 'new game', 'adventure']):
            session['game_state'] = 'tavern'
            return ("You enter the Prancing Pony, a lively tavern in the town of Bree. "
                   "The tavern is bustling with activity. In the corner, you notice a "
                   "hooded figure watching you intently. The bartender nods in your direction. "
                   "What would you like to do?")
        return ("Welcome to AI Dungeon Master! I'm here to guide you through a D&D 5e adventure. "
               "Would you like to start a new game or create a character first?")
    
    if game_state == 'tavern':
        if any(word in message_lower for word in ['talk', 'bartender', 'speak']):
            return ("You approach the bartender, a stout halfling with a friendly smile. "
                   "\"What can I do for ya, traveler?\" he asks, wiping a mug with a cloth.")
        
        if any(word in message_lower for word in ['hooded', 'figure', 'corner', 'stranger']):
            session['game_state'] = 'quest_offer'
            return ("You approach the hooded figure. As you get closer, they pull back their hood "
                   "slightly, revealing the face of an elderly elven woman with silvery eyes. "
                   "\"I've been waiting for someone like you,\" she says in a hushed voice. "
                   "\"I have a task that requires someone with your... unique abilities.\"")
    
    if game_state == 'quest_offer':
        if any(word in message_lower for word in ['accept', 'yes', 'tell me', 'what task']):
            session['game_state'] = 'quest_details'
            return ("The elf leans in closer. \"There is an ancient artifact hidden in the ruins of "
                   "Stonehollow, just north of here. It's said to be guarded by traps and perhaps "
                   "something more sinister. Retrieve it, and you'll be rewarded handsomely.\" "
                   "She slides a small map across the table. \"Will you accept this quest?\"")
    
    # Default responses based on keywords
    if any(word in message_lower for word in ['attack', 'fight', 'hit']):
        return "Roll for initiative! What are you attacking and with what weapon?"
    
    if any(word in message_lower for word in ['look', 'examine', 'inspect']):
        return "You look around carefully. What specifically are you trying to examine?"
    
    # Fallback response
    return ("FALLBACK RESPONSE: I understand you want to " + message[:20] + "... " +
           "In a full implementation, I would use an AI language model to generate "
           "a contextually appropriate DM response.")

if __name__ == '__main__':
    # Print available routes
    print("\nAvailable routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule}")
    
    print("\nStarting Flask server...")
    # Run with host 0.0.0.0 to make it accessible from other devices
    app.run(debug=True, host='0.0.0.0', port=5000)