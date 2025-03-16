"""
Simple script to test if environment variables are being loaded correctly
"""

import os
from dotenv import load_dotenv

print("=== Environment Variable Test ===")
print(f"Current working directory: {os.getcwd()}")

# Check if .env file exists
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")

# Try to load environment variables
print("\nAttempting to load environment variables from .env file...")
load_dotenv()
print("Environment variables loaded (if .env file exists)")

# Check for API key and model
api_key = os.getenv('AI_API_KEY')
api_model = os.getenv('AI_MODEL')

print(f"\nAPI_KEY found: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"API_KEY starts with: {api_key[:8]}... (length: {len(api_key)})")
    has_quotes = api_key.startswith('"') or api_key.startswith("'")
    print(f"API_KEY contains quotes: {'Yes' if has_quotes else 'No'}")

print(f"AI_MODEL found: {'Yes' if api_model else 'No'}")
if api_model:
    print(f"AI_MODEL value: {api_model}")

print("\n=== Test Complete ===")

# Try to import and initialize XAIHandler
print("\nAttempting to import XAIHandler...")
try:
    from xai_handler import XAIHandler
    print("XAIHandler imported successfully")
    
    if api_key:
        print("Attempting to initialize XAIHandler...")
        handler = XAIHandler(api_key, api_model or 'grok-1')
        print("XAIHandler initialized successfully")
    else:
        print("Cannot initialize XAIHandler: No API key available")
        
except ImportError as e:
    print(f"ImportError: {e}")
    print("Make sure xai_handler.py is in the same directory as this script")
except Exception as e:
    print(f"Error initializing XAIHandler: {e}")
    import traceback
    traceback.print_exc()