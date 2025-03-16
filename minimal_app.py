"""
Minimal Flask app to test AI handler initialization
"""

from flask import Flask, jsonify
import os
from dotenv import load_dotenv
from xai_handler import XAIHandler

# Create Flask app
app = Flask(__name__)

# Print debug information
print("=== Starting Minimal Flask App ===")
print(f"Current working directory: {os.getcwd()}")

# Load environment variables
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")
load_dotenv()

# Get API credentials
api_key = os.getenv('AI_API_KEY')
api_model = os.getenv('AI_MODEL', 'grok-1')

print(f"API_KEY found: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API_KEY starts with: {api_key[:8]}...")
print(f"AI_MODEL: {api_model}")

# Initialize AI handler
try:
    print("Initializing AI handler...")
    ai_handler = XAIHandler(api_key, api_model)
    print("AI handler initialized successfully!")
    handler_available = True
except Exception as e:
    print(f"Error initializing AI handler: {e}")
    ai_handler = None
    handler_available = False

# Define a simple route
@app.route('/')
def index():
    return "Minimal Flask App is running!"

# Define a test route for the AI handler
@app.route('/test-ai')
def test_ai():
    if handler_available:
        try:
            response = ai_handler.generate_response(
                player_message="Hello, Dungeon Master!",
                conversation_history=[],
                game_state="intro"
            )
            return jsonify({
                "success": True,
                "ai_response": response
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": str(e)
            })
    else:
        return jsonify({
            "success": False,
            "error": "AI handler not available"
        })

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)