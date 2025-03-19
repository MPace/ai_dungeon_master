from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import os
import json
import random
from datetime import datetime
import uuid
from dotenv import load_dotenv
from xai_handler import XAIHandler
from db import init_db, close_db, get_db
from character_data import save_character, get_character, list_characters, delete_character
import functools
import bcrypt
from bson.objectid import ObjectId
import logging

# Initialize Flask app
app = Flask(__name__,
           static_folder='static',
           template_folder='templates')
app.secret_key = os.urandom(24)  # For session management

# Initialize database connection
print("Initializing database connection...")
db_available = init_db()

# Ensure directory structure exists
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/images', exist_ok=True)
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


# Logging setup
logging.basicConfig(
    filename='/var/www/ai_dungeon_master/app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# User authentication decorator
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Landing page with login form
@app.route('/')
def index():
    # If user is already logged in, redirect to dashboard
    if 'user_id' in session:
        return redirect(url_for('user_dashboard'))
    return render_template('index.html')


# User login endpoint
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    logger.info("=============================================")
    logger.info(f"Login attempt for user: {username}")
    
    if not username or not password:
        logger.error("Missing username or password")
        flash('Username and password are required', 'error')
        return redirect(url_for('index'))
    
    try:
        db = get_db()
        if db is None:
            logger.error("Database connection failed in login")
            flash('Database connection error', 'error')
            return redirect(url_for('index'))
        
        logger.info(f"Searching for user '{username}' in database...")
        user_count = db.users.count_documents({})
        logger.info(f"Total users in database: {user_count}")
        
        all_users = list(db.users.find({}, {"username": 1}))
        logger.info(f"All usernames in database: {[u.get('username') for u in all_users]}")
        
        user = db.users.find_one({'username': username})
        logger.info(f"User found in database: {user is not None}")
        
        if user:
            logger.info(f"User details: id={user.get('_id')}, username={user.get('username')}")
            stored_hash = user.get('password_hash', '')
            password_bytes = password.encode('utf-8')
            hash_type = "bcrypt" if stored_hash.startswith('$2') else "sha256"
            logger.info(f"Stored hash type: {hash_type}")
            logger.info("Attempting to verify password...")
            
            is_valid = verify_password(password, stored_hash)
            logger.info(f"Password verification result: {is_valid}")
            
            if is_valid:
                logger.info("Password valid, setting up session...")
                session['user_id'] = str(user.get('_id'))
                session['username'] = user.get('username')
                logger.info(f"Session data set: user_id={session.get('user_id')}, username={session.get('username')}")
                flash('Login successful!', 'success')
                logger.info("Redirecting to dashboard...")
                return redirect(url_for('user_dashboard'))
            else:
                logger.error("Password verification failed!")
        else:
            logger.error(f"No user found with username '{username}'")
        
        logger.error("Login failed, redirecting to index")
        flash('Invalid username or password', 'error')
        return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Login exception: {str(e)}")
        import traceback
        traceback.print_exc(file=open('/var/www/ai_dungeon_master/app.log', 'a'))
        flash('An error occurred during login. Please try again.', 'error')
        return redirect(url_for('index'))
    finally:
        logger.info("=============================================")


# User registration endpoint
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    
    print("============ REGISTRATION ATTEMPT ============")
    print(f"Attempting to register username: {username}, email: {email}")
    
    # Validate inputs
    if not username or not password or not email:
        print("Missing required fields")
        flash('All fields are required', 'error')
        return redirect(url_for('index'))
    
    # Validate username format (alphanumeric, no spaces)
    if not username.isalnum():
        print("Username not alphanumeric")
        flash('Username must contain only letters and numbers', 'error')
        return redirect(url_for('index'))
    
    # Validate password strength (at least 8 characters)
    if len(password) < 8:
        print("Password too short")
        flash('Password must be at least 8 characters long', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get database connection
        print("Getting database connection...")
        db = get_db()
        if db is None:
            print("Database connection failed")
            flash('Database connection error', 'error')
            return redirect(url_for('index'))
        
        print("Checking if username exists...")
        # Check if username already exists
        existing_user = db.users.find_one({'username': username})
        if existing_user:
            print(f"Username {username} already exists")
            flash('Username already exists', 'error')
            return redirect(url_for('index'))
        
        print("Checking if email exists...")
        # Check if email already exists
        existing_email = db.users.find_one({'email': email})
        if existing_email:
            print(f"Email {email} already registered")
            flash('Email already registered', 'error')
            return redirect(url_for('index'))
        
        # Create new user
        print("Creating new user...")
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        print("Hashing password...")
        try:
            password_hash = hash_password(password)
            print(f"Password hashed successfully. Hash type: {'bcrypt' if password_hash.startswith('$2') else 'sha256'}")
        except Exception as hash_error:
            print(f"Password hashing error: {hash_error}")
            import traceback
            traceback.print_exc()
            raise  # Re-raise to be caught by outer exception handler
        
        new_user = {
            'user_id': user_id,
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created_at': created_at,
            'last_login': created_at
        }
        
        print(f"Inserting user into database: {new_user}")
        # Insert user into database
        result = db.users.insert_one(new_user)
        
        print(f"Insert result: {result.inserted_id is not None}")
        
        if result.inserted_id:
            # Log user in
            print("Setting up session...")
            session['user_id'] = user_id
            session['username'] = username
            
            print(f"User registered successfully: {username}")
            flash('Registration successful! Welcome to AI Dungeon Master.', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            print("Failed to insert user into database")
            flash('Failed to create user account', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        print(f"Registration error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for('index'))
    finally:
        print("============================================")

    

# User logout endpoint
@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

# Helper functions for authentication
# Better password hashing with bcrypt
def hash_password(password):
    """
    Hash a password with bcrypt for secure storage
    """
    try:
        # Generate a salt and hash the password
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        # Return the hash as a string
        return password_hash.decode('utf-8')
    except Exception as e:
        print(f"Error hashing password: {e}")
        # Fallback to a less secure method if bcrypt is unavailable
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """
    Verify a password against a stored hash
    """
    try:
        # Check if this is a bcrypt hash
        if password_hash.startswith('$2'):
            # Bcrypt password check
            password_bytes = password.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hash_bytes)
        else:
            # Fallback SHA-256 check for legacy passwords
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == password_hash
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False

# Test database connection
@app.route('/test-db-connection')
def test_db_connection():
    """
    Test endpoint to verify database connection
    Only accessible in development mode
    """
    if os.getenv('FLASK_ENV') != 'development':
        return jsonify({
            'success': False,
            'message': 'This endpoint is only available in development mode'
        }), 403
    
    try:
        db = get_db()
        if db is None:
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'mongo_uri': os.getenv('MONGO_URI', 'Not set').replace('mongodb+srv://', 'mongodb+srv://****:****@')
            })
        
        # Try to get collections and count documents
        collections = db.list_collection_names()
        users_count = db.users.count_documents({})
        
        return jsonify({
            'success': True,
            'message': 'Database connection successful',
            'collections': collections,
            'users_count': users_count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Database error: {str(e)}',
            'mongo_uri': os.getenv('MONGO_URI', 'Not set').replace('mongodb+srv://', 'mongodb+srv://****:****@')
        })

@app.route('/test-bcrypt')
def test_bcrypt():
    try:
        import bcrypt
        test_password = "test123"
        
        # Test encoding and hashing
        password_bytes = test_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        hash_str = hashed.decode('utf-8')
        
        # Test verification
        is_valid = bcrypt.checkpw(password_bytes, hashed)
        
        return jsonify({
            'success': True,
            'message': 'Bcrypt is working correctly',
            'password': test_password,
            'hash': hash_str,
            'verification': is_valid
        })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        
        return jsonify({
            'success': False,
            'message': 'Bcrypt test failed',
            'error': str(e),
            'traceback': error_traceback
        })



# User dashboard
@app.route('/dashboard')
@login_required
def user_dashboard():
    """User dashboard showing characters and drafts"""
    # Get user's ID from session
    user_id = session.get('user_id')
    
    try:
        db = get_db()
        
        # Get completed characters (not drafts)
        characters = list(db.characters.find({
            'user_id': user_id,
            '$or': [
                {'isDraft': False},
                {'isDraft': {'$exists': False}}  # For older characters without the field
            ]
        }).sort('last_played', -1))
        
        # Convert ObjectId to string for serialization
        for character in characters:
            character['_id'] = str(character['_id'])
            
            # Format dates for display
            if 'updated_at' in character:
                character['updated_at'] = character['updated_at'].strftime('%Y-%m-%d %H:%M') \
                    if isinstance(character['updated_at'], datetime) \
                    else character['updated_at']
                    
            if 'created_at' in character:
                character['created_at'] = character['created_at'].strftime('%Y-%m-%d %H:%M') \
                    if isinstance(character['created_at'], datetime) \
                    else character['created_at']
                    
            if 'last_played' in character:
                character['last_played'] = character['last_played'].strftime('%Y-%m-%d %H:%M') \
                    if isinstance(character['last_played'], datetime) \
                    else character['last_played']
        
        # Get draft characters (only true drafts that don't have completed versions)
        draft_query = {
            'user_id': user_id,
            'isDraft': True
        }
        
        # Get character_ids of completed characters to exclude any drafts that were completed
        completed_character_ids = [char['character_id'] for char in characters if 'character_id' in char]
        if completed_character_ids:
            draft_query['character_id'] = {'$nin': completed_character_ids}
        
        drafts = list(db.character_drafts.find(draft_query).sort('lastUpdated', -1))
        
        # Convert ObjectId to string for serialization
        for draft in drafts:
            draft['_id'] = str(draft['_id'])
            
            # Format dates for display
            if 'lastUpdated' in draft:
                try:
                    # Try to parse the ISO string if it's a string
                    if isinstance(draft['lastUpdated'], str):
                        from dateutil import parser
                        draft['lastUpdated'] = parser.parse(draft['lastUpdated']).strftime('%Y-%m-%d %H:%M')
                    # Or format it if it's already a datetime
                    elif isinstance(draft['lastUpdated'], datetime):
                        draft['lastUpdated'] = draft['lastUpdated'].strftime('%Y-%m-%d %H:%M')
                except:
                    # Keep as is if we can't parse it
                    pass
        
        print(f"Found {len(characters)} completed characters and {len(drafts)} drafts")
        
        return render_template('user.html', 
                              username=session.get('username', 'User'),
                              characters=characters,
                              drafts=drafts)
                              
    except Exception as e:
        print(f"Error in user_dashboard: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard: ' + str(e), 'error')
        return render_template('user.html',
                              username=session.get('username', 'User'),
                              characters=[],
                              drafts=[])
    # Get user's characters
    db = get_db()
    characters = list(db.characters.find({'user_id': session['user_id']}))
    
    # Convert ObjectId to string for serialization
    for character in characters:
        character['_id'] = str(character['_id'])
    
    # Get draft characters
    drafts = list(db.character_drafts.find({
        'user_id': session['user_id'],
        'isDraft': True
    }))
    
    # Convert ObjectId to string for serialization
    for draft in drafts:
        draft['_id'] = str(draft['_id'])
    
    return render_template('user.html', 
                          username=session['username'],
                          characters=characters,
                          drafts=drafts)

# Character creation page
@app.route('/create')
@login_required
def create_character():
    # Check if we're loading a draft
    draft_id = request.args.get('draft_id')
    draft = None
    
    if draft_id:
        db = get_db()
        draft = db.character_drafts.find_one({
            'character_id': draft_id,
            'user_id': session['user_id']
        })
        
        if draft:
            # Convert ObjectId to string for serialization
            draft['_id'] = str(draft['_id'])
    
    return render_template('create.html', draft=draft)

# Game interface page
@app.route('/play/<character_id>')
@login_required
def play_game(character_id):
    """Game interface page for playing with a specific character"""
    # Get user_id from session
    user_id = session.get('user_id')
    
    try:
        print(f"Loading character {character_id} for user {user_id}")
        
        # Get character data
        db = get_db()
        character = db.characters.find_one({
            'character_id': character_id
        })
        
        if not character:
            print(f"Character not found: {character_id}")
            flash('Character not found', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Check if this character belongs to the current user
        if character.get('user_id') != user_id:
            print(f"Character {character_id} belongs to user {character.get('user_id')}, not {user_id}")
            flash('You do not have permission to access this character', 'error')
            return redirect(url_for('user_dashboard'))
        
        # Convert ObjectId to string for JSON serialization
        character['_id'] = str(character['_id'])
        
        print(f"Character loaded successfully: {character.get('name')}")
        
        # Update last played timestamp
        db.characters.update_one(
            {'character_id': character_id},
            {'$set': {'last_played': datetime.utcnow()}}
        )
        
        return render_template('dm.html', character=character)
    
    except Exception as e:
        print(f"Error in play_game route: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading character: ' + str(e), 'error')
        return redirect(url_for('user_dashboard'))
    # Get character data

@app.route('/test-mongo-insert')
def test_mongo_insert():
    try:
        db = get_db()
        if db is None:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            })
        
        # Try a simple insert and query
        test_doc = {
            'test_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow(),
            'data': 'Test document'
        }
        
        result = db.test_collection.insert_one(test_doc)
        
        if result.inserted_id:
            # Try to retrieve the document
            found = db.test_collection.find_one({'_id': result.inserted_id})
            
            return jsonify({
                'success': True,
                'message': 'MongoDB insert test successful',
                'document_id': str(result.inserted_id),
                'document_retrieved': found is not None
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to insert test document'
            })
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        
        return jsonify({
            'success': False,
            'message': 'MongoDB test failed',
            'error': str(e),
            'traceback': error_traceback
        })


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
    character_data = data.get('character_data')
    
    print(f"\n--- New message received: '{message}' ---")
    
    # If no session ID or invalid, create a new session
    if not session_id or session_id not in SESSIONS_DB:
        session_id = str(uuid.uuid4())
        SESSIONS_DB[session_id] = {
            'history': [],
            'character': character_data,  # Store character data in the session
            'game_state': 'intro'
        }
        print(f"Created new session: {session_id}")
    else:
        print(f"Using existing session: {session_id}")
        # Update character data if provided
        if character_data:
            SESSIONS_DB[session_id]['character'] = character_data
    
    # Add player message to history
    SESSIONS_DB[session_id]['history'].append({
        'sender': 'player',
        'message': message,
        'timestamp': datetime.now().isoformat()
    })
    
    # Process the message and generate a response
    if ai_handler:
        print(f"Using AI handler with model: {AI_MODEL}")
        
        # Create a system prompt that includes character information
        character_info = ""
        if SESSIONS_DB[session_id]['character']:
            char = SESSIONS_DB[session_id]['character']
            character_info = f"The player's character is named {char.get('name', 'Unknown')}, "
            character_info += f"a level {char.get('level', '1')} {char.get('race', 'Unknown')} {char.get('class', 'Unknown')} "
            character_info += f"with the following abilities: "
            
            abilities = char.get('abilities', {})
            for ability_name, score in abilities.items():
                modifier = (score - 10) // 2
                sign = "+" if modifier >= 0 else ""
                character_info += f"{ability_name.capitalize()}: {score} ({sign}{modifier}), "
            
            character_info += f"with proficiency in the following skills: {', '.join(char.get('skills', []))}. "
            
            if char.get('description'):
                character_info += f"Character description: {char['description']}"
        
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

@app.route('/api/save-character', methods=['POST'])
def save_character_route():
    """API endpoint to save a character"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Get character data from request
        character_data = request.json
        
        if character_data is None:
            print("No character data received")
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        if user_id is None:
            print("No user_id in session")
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Check for submission ID to prevent duplicate saves
        submission_id = character_data.get('submissionId')
        
        if submission_id is not None:
            # Check if we've seen this submission before
            db = get_db()
            if db is not None:
                recent_submission = db.submission_log.find_one({
                    'submission_id': submission_id,
                    'user_id': user_id
                })
                
                if recent_submission is not None:
                    # This is a duplicate submission, return the same character_id but don't save again
                    print(f"Detected duplicate submission: {submission_id}")
                    return jsonify({
                        'success': True,
                        'character_id': recent_submission.get('character_id'),
                        'message': 'Character already saved (duplicate submission)',
                        'isDuplicate': True
                    })
        
        # Add user_id to character data
        character_data['user_id'] = user_id
        
        # Mark as complete (not a draft)
        character_data['isDraft'] = False
        character_data['completedAt'] = datetime.utcnow().isoformat()
        
        print(f"Saving character: {character_data.get('name')} for user {user_id}")
        
        # Get the character_id
        character_id = character_data.get('character_id')
        
        if character_id is None:
            # Generate a new ID if none exists
            character_id = str(uuid.uuid4())
            character_data['character_id'] = character_id
            print(f"Generated new character_id: {character_id}")
        
        # First, check if this character already exists in the main collection
        db = get_db()
        if db is not None:
            existing_character = db.characters.find_one({
                'character_id': character_id,
                'user_id': user_id
            })
            
            if existing_character is not None and existing_character.get('isDraft') is not True:
                # This character already exists as a completed character
                print(f"Character already exists: {character_id}")
                
                # Log this submission to prevent future duplicates
                if submission_id is not None:
                    db.submission_log.insert_one({
                        'submission_id': submission_id,
                        'character_id': character_id,
                        'user_id': user_id,
                        'timestamp': datetime.utcnow()
                    })
                
                # Return success but don't save again
                return jsonify({
                    'success': True,
                    'character_id': character_id,
                    'message': 'Character already exists',
                    'alreadyExists': True
                })
        
            # Delete any existing drafts with this ID
            if db is not None:
                db.character_drafts.delete_many({
                    'character_id': character_id
                })
                
                # Ensure there are no duplicates in the characters collection
                db.characters.delete_many({
                    'character_id': character_id,
                    'isDraft': True
                })
        
        # Now save the character
        saved_id = save_character(character_data, user_id)
        
        if saved_id is not None:
            print(f"Character saved successfully with ID: {saved_id}")
            
            # Log this submission to prevent future duplicates
            if submission_id is not None and db is not None:
                # Create submission_log collection if it doesn't exist
                if 'submission_log' not in db.list_collection_names():
                    db.create_collection('submission_log')
                    # Add TTL index to auto-expire log entries after 1 day
                    db.submission_log.create_index("timestamp", expireAfterSeconds=86400)
                
                db.submission_log.insert_one({
                    'submission_id': submission_id,
                    'character_id': saved_id,
                    'user_id': user_id,
                    'timestamp': datetime.utcnow()
                })
            
            return jsonify({
                'success': True,
                'character_id': saved_id,
                'message': 'Character saved successfully'
            })
        else:
            print("Failed to save character")
            return jsonify({
                'success': False,
                'error': 'Failed to save character'
            }), 500
    
    except Exception as e:
        print(f"Error in save_character_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
def save_character_route():
    """API endpoint to save a character"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Log request for debugging
        print("Received save-character request")
        
        # Get character data from request
        character_data = request.json
        
        if not character_data:
            print("No character data received")
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            print("No user_id in session")
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Add user_id to character data
        character_data['user_id'] = user_id
        
        # Mark as complete (not a draft)
        character_data['isDraft'] = False
        character_data['completedAt'] = datetime.utcnow().isoformat()
        
        # Log character info
        print(f"Saving character: {character_data.get('name')} for user {user_id}")
        
        # Get the character_id
        character_id = character_data.get('character_id')
        
        # If there's a character_id, explicitly clean up any drafts first
        if character_id:
            db = get_db()
            
            # First, explicitly delete from drafts collection
            result = db.character_drafts.delete_many({
                'character_id': character_id
            })
            print(f"Explicitly deleted {result.deleted_count} drafts for character_id: {character_id}")
            
            # Also check if there's an existing character and delete it to avoid duplicates
            existing_chars = db.characters.find({
                'character_id': character_id,
                'isDraft': True
            })
            
            existing_count = 0
            for _ in existing_chars:
                existing_count += 1
            
            if existing_count > 0:
                result = db.characters.delete_many({
                    'character_id': character_id, 
                    'isDraft': True
                })
                print(f"Deleted {result.deleted_count} draft characters from characters collection")
        
        # Now save the character
        character_id = save_character(character_data, user_id)
        
        if character_id:
            print(f"Character saved successfully with ID: {character_id}")
            return jsonify({
                'success': True,
                'character_id': character_id,
                'message': 'Character saved successfully'
            })
        else:
            print("Failed to save character")
            return jsonify({
                'success': False,
                'error': 'Failed to save character'
            }), 500
    
    except Exception as e:
        print(f"Error in save_character_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    """API endpoint to save a character"""
    if  db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Log request for debugging
        print("Received save-character request")
        
        # Get character data from request
        character_data = request.json
        
        if not character_data:
            print("No character data received")
            return jsonify({
                'success': False,
                'error': 'No character data provided'
            }), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            print("No user_id in session")
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Add user_id to character data
        character_data['user_id'] = user_id
        
        # Mark as complete (not a draft)
        character_data['isDraft'] = False
        character_data['completedAt'] = datetime.utcnow().isoformat()
        
        # Log character info
        print(f"Saving character: {character_data.get('name')} for user {user_id}")
        
        # If it was a draft, delete the draft version
        if 'character_id' in character_data:
            db = get_db()
            db.character_drafts.delete_one({
                'character_id': character_data['character_id'],
                'user_id': user_id
            })
            print(f"Deleted draft for character_id: {character_data['character_id']}")
        
        # Save the character
        character_id = save_character(character_data, user_id)
        
        if character_id:
            print(f"Character saved successfully with ID: {character_id}")
            return jsonify({
                'success': True,
                'character_id': character_id,
                'message': 'Character saved successfully'
            })
        else:
            print("Failed to save character")
            return jsonify({
                'success': False,
                'error': 'Failed to save character'
            }), 500
    
    except Exception as e:
        print(f"Error in save_character_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    
    """API endpoint to save a character"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    character_data = request.json
    
    # TODO: Get user_id from session when authentication is implemented
    user_id = None
    
    character_id = save_character(character_data, user_id)
    
    if character_id:
        return jsonify({
            'success': True,
            'character_id': character_id
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to save character'
        })

@app.route('/api/character/<character_id>', methods=['GET'])
def get_character_route(character_id):
    """API endpoint to retrieve a character"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    character = get_character(character_id)
    
    if character:
        return jsonify({
            'success': True,
            'character': character
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Character not found'
        })

@app.route('/api/characters', methods=['GET'])
def list_characters_route():
    """API endpoint to list characters"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        })
    
    # TODO: Get user_id from session when authentication is implemented
    user_id = None
    
    characters = list_characters(user_id)
    
    return jsonify({
        'success': True,
        'characters': characters
    })

@app.route('/api/delete-character/<character_id>', methods=['POST'])
@login_required
def delete_character_route(character_id):
    """API endpoint to delete a character"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Check if character exists and belongs to the user
        db = get_db()
        character = db.characters.find_one({
            'character_id': character_id,
            'user_id': user_id
        })
        
        if not character:
            return jsonify({
                'success': False,
                'error': 'Character not found or access denied'
            }), 404
        
        # Delete the character
        result = delete_character(character_id)
        
        if result:
            # Also delete any drafts with this character_id
            db.character_drafts.delete_many({
                'character_id': character_id,
                'user_id': user_id
            })
            
            return jsonify({
                'success': True,
                'message': f"Character '{character.get('name', 'Unknown')}' deleted successfully"
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete character'
            }), 500
    
    except Exception as e:
        print(f"Error in delete_character_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/delete-draft/<draft_id>', methods=['POST'])
@login_required
def delete_draft_route(draft_id):
    """API endpoint to delete a character draft"""
    if db_available is not True:
        return jsonify({
            'success': False,
            'error': 'Database not available'
        }), 500
    
    try:
        # Get user_id from session
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not logged in'
            }), 401
        
        # Check if draft exists and belongs to the user
        db = get_db()
        draft = db.character_drafts.find_one({
            'character_id': draft_id,
            'user_id': user_id
        })
        
        if not draft:
            return jsonify({
                'success': False,
                'error': 'Draft not found or access denied'
            }), 404
        
        # Delete the draft
        result = db.character_drafts.delete_one({
            'character_id': draft_id,
            'user_id': user_id
        })
        
        if result.deleted_count > 0:
            draft_name = draft.get('name', 'Unnamed draft')
            return jsonify({
                'success': True,
                'message': f"Draft '{draft_name}' deleted successfully"
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete draft'
            }), 500
    
    except Exception as e:
        print(f"Error in delete_draft_route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/test-session')
def test_session():
    if 'test_count' not in session:
        session['test_count'] = 1
    else:
        session['test_count'] += 1
    
    return jsonify({
        'success': True,
        'message': f'Session is working! Count: {session["test_count"]}',
        'session_data': {k: session[k] for k in session}
    })


def generate_dm_response(message, session):
    """
    Generate a DM response based on the player's message and session state
    This is a fallback function used when the AI is not available
    """
    message_lower = message.lower()
    game_state = session.get('game_state', 'intro')
    character = session.get('character', {})
    character_name = character.get('name', 'adventurer') if character else 'adventurer'
    
    print("WARNING: Using fallback response generator instead of AI!")
    
    # Very simple rule-based response for demonstration
    if game_state == 'intro':
        if any(word in message_lower for word in ['start', 'begin', 'new game', 'adventure']):
            session['game_state'] = 'tavern'
            return (f"Well met, {character_name}! You enter the Prancing Pony, a lively tavern in the town of Bree. "
                   "The tavern is bustling with activity. In the corner, you notice a "
                   "hooded figure watching you intently. The bartender nods in your direction. "
                   "What would you like to do?")
        return (f"Welcome, {character_name}! I'm here to guide you through a D&D 5e adventure. "
               "Would you like to start a new game or create a character first?")
    
    if game_state == 'tavern':
        if any(word in message_lower for word in ['talk', 'bartender', 'speak']):
            return ("You approach the bartender, a stout halfling with a friendly smile. "
                   f"\"What can I do for ya, {character_name}?\" he asks, wiping a mug with a cloth.")
        
        if any(word in message_lower for word in ['hooded', 'figure', 'corner', 'stranger']):
            session['game_state'] = 'quest_offer'
            return ("You approach the hooded figure. As you get closer, they pull back their hood "
                   "slightly, revealing the face of an elderly elven woman with silvery eyes. "
                   f"\"I've been waiting for someone like you, {character_name},\" she says in a hushed voice. "
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
        return f"Roll for initiative, {character_name}! What are you attacking and with what weapon?"
    
    if any(word in message_lower for word in ['look', 'examine', 'inspect']):
        return f"You look around carefully. What specifically are you trying to examine, {character_name}?"
    
    # Fallback response
    return (f"FALLBACK RESPONSE: I understand you want to {message[:20]}... "
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