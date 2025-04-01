"""
Game routes
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.game import game_bp
from app.services.game_service import GameService
from app.services.character_service import CharacterService
from app.extensions import get_db
from functools import wraps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Checking authentication for route: {request.path}")
        logger.info(f"Session contents: {dict(session)}")
        if 'user_id' not in session:
            logger.error(f"AUTHENTICATION FAILED: No user_id in session for {request.path}")
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.index'))
            
        # Authentication successful
        logger.info(f"Authentication successful for user: {session.get('username', 'Unknown')}")
        return f(*args, **kwargs)
    return decorated_function

@game_bp.route('/user_dashboard')
@game_bp.route('/dashboard')
@login_required
def dashboard():
    # Get user ID from session
    user_id = session.get('user_id')
    
    characters = []
    drafts = []

    try:
        # Get characters 
        character_result = CharacterService.list_characters(user_id)
        if character_result['success']:
            characters = character_result['characters']
        else:
            error_msg = character_result.get('error', 'Unknown error')
            logger.error(f"Error loading characters: {error_msg}")
            flash(f"Error loading characters: {error_msg}", 'error')

         # Get drafts
        drafts_result = CharacterService.list_character_drafts(user_id)
        if drafts_result['success']:
            drafts = drafts_result['drafts']
            logger.info(f"Successfully loaded {len(drafts)} drafts")
        else:
            error_msg = drafts_result.get('error', 'Unknown error')
            logger.error(f"Error loading drafts: {error_msg}")
            flash(f'Error loading drafts: {error_msg}', 'error')
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        flash('Error loading dashboard: ' + str(e), 'error')
    
    return render_template('user.html',
                              username=session.get('username', 'User'),
                              characters=characters,
                              drafts=drafts)

@game_bp.route('/play/<character_id>')
@login_required
def play_game(character_id):
    # Get user_id from session
    user_id = session.get('user_id')
    logger.info(f"Loading character {character_id} for user {user_id}")
    
    try:
        # Get character data
        character_result = CharacterService.get_character(character_id, user_id)
        
        if not character_result.get('success', False):
            logger.warning(f"Character not found: {character_id}")
            flash('Character not found', 'error')
            return redirect(url_for('game.dashboard'))
        
        character = character_result.get('character')
        if not character:
            logger.warning(f"Character object is None: {character_id}")
            flash('Error loading character', 'error')
            return redirect(url_for('game.dashboard'))
        
        logger.info(f"Character loaded successfully: {character.name}")
        
        # Convert the Character object to a dictionary for JSON serialization
        character_dict = character.to_dict()
        
        # Log character data for debugging
        logger.info(f"Character dictionary has keys: {character_dict.keys()}")
        
        # Update last played timestamp
        try:
            character.last_played = datetime.utcnow()
            character_dict = character.to_dict()  # Update the dictionary with new timestamp
            
            # Save the updated timestamp
            db = get_db()
            if db is not None:
                db.characters.update_one(
                    {'character_id': character_id},
                    {'$set': {'last_played': datetime.utcnow()}}
                )
        except Exception as e:
            logger.warning(f"Error updating last_played timestamp: {e}")
        
        return render_template('dm.html', character=character_dict)
    
    except Exception as e:
        logger.error(f"Error in play_game route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        flash('Error loading character: ' + str(e), 'error')
        return redirect(url_for('game.dashboard'))

@game_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Process a message from the player and return a DM response asynchronously"""
    try:
        data = request.json
        message = data.get('message', '')
        session_id = data.get('session_id')
        character_data = data.get('character_data')
        
        user_id = session.get('user_id')
        
        # Validate required inputs
        if not message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
            
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401

        # Submit task to Celery
        from app.tasks import process_dm_message
        task = process_dm_message.delay(message, session_id, character_data, user_id)
        
        # Return task ID immediately
        return jsonify({
            'success': True,
            'task_id': task.id,
            'status': 'processing',
            'message': 'Your message is being processed by the DM. Please wait for the response.'
        })
        
    except Exception as e:
        logger.error(f"Unhandled exception in send_message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f"Server error: {str(e)}"
        }), 500

@game_bp.route('/api/roll-dice', methods=['POST'])
@login_required
def roll_dice():
    """Handle dice rolling requests"""
    try:
        data = request.json
        dice_type = data.get('dice', 'd20')
        modifier = data.get('modifier', 0)
        
        # Get user and session info
        user_id = session.get('user_id')
        session_id = data.get('session_id')
        
        # Roll the dice
        result = GameService.roll_dice(
            dice_type=dice_type, 
            modifier=modifier,
            user_id=user_id,
            session_id=session_id
        )
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify({
                'error': result.get('error', 'Failed to roll dice')
            }), 400
    except Exception as e:
        logger.error(f"Error in roll_dice route: {e}")
        return jsonify({
            'error': f"Server error: {str(e)}"
        }), 500
    

@game_bp.route('/api/check-task/<task_id>', methods=['GET'])
@login_required
def check_task(task_id):
    """Check the status of a Celery task"""
    try:
        from celery.result import AsyncResult
        from app.celery_config import celery
        
        # Get the task result
        task = AsyncResult(task_id, app=celery)
        
        # Check task state
        if task.state == 'PENDING':
            # Task is still pending
            response = {
                'success': True,
                'status': 'processing',
                'message': 'The Dungeon Master is still crafting a response...'
            }
        elif task.state == 'FAILURE':
            # Task failed
            response = {
                'success': False,
                'status': 'error',
                'error': str(task.info)
            }
        elif task.state == 'SUCCESS':
            # Task completed successfully
            response = {
                'success': True,
                'status': 'completed',
                'result': task.result
            }
        else:
            # Other states (STARTED, RETRY, etc.)
            response = {
                'success': True,
                'status': 'processing',
                'message': f'Task is in state: {task.state}'
            }
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f"Error checking task status: {str(e)}"
        }), 500