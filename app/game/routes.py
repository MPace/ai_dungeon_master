# app/game/routes.py
"""
Game routes
"""
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from app.game import game_bp
from app.services.game_service import GameService
from app.services.character_service import CharacterService
from app.extensions import get_db
from app.langgraph_core.graph import get_manager  # Add this import
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

    logger.info(f"Dashboard access redirecting to React dashboard for user ID: {user_id}")

    return redirect(url_for('dashboard.index'))

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
        
        # Store character_id in session
        session['character_id'] = character_id
        
        # Get or create game session
        db = get_db()
        game_session = None
        
        if db is not None:
            # First, check if there's an existing active game session
            game_session = db.sessions.find_one({
                'character_id': character_id,
                'user_id': user_id,
                'status': {'$ne': 'completed'}  # Not completed
            })
            
            if game_session:
                logger.info(f"Found existing game session: {game_session.get('session_id')}")
            else:
                # Create a new game session
                logger.info("Creating new game session")
                
                # Get world_id and campaign_module_id from character data
                world_id = character_dict.get('world_id')
                campaign_module_id = character_dict.get('campaign_id') or character_dict.get('campaign_module_id')
                
                # If not in character data, use defaults or let the user choose
                if not world_id:
                    world_id = 'forgotten_realms'  # Default world
                
                # Create the session using GameService
                session_result = GameService.create_session(
                    character_id=character_id,
                    user_id=user_id,
                    world_id=world_id,
                    campaign_module_id=campaign_module_id
                )
                
                if session_result.get('success'):
                    game_session = session_result.get('session')
                    logger.info(f"Created new game session: {game_session.session_id}")
                else:
                    logger.error(f"Failed to create game session: {session_result.get('error')}")
                    flash('Error creating game session', 'error')
                    return redirect(url_for('game.dashboard'))
        
        # Store all necessary IDs in Flask session
        if game_session:
            session['session_id'] = game_session.get('session_id')
            session['world_id'] = game_session.get('world_id')
            session['campaign_module_id'] = game_session.get('campaign_module_id')
        else:
            # Fallback if no database connection
            session['session_id'] = str(uuid.uuid4())
            session['world_id'] = character_dict.get('world_id', 'forgotten_realms')
            session['campaign_module_id'] = character_dict.get('campaign_id')
        
        # User ID should already be in session from login
        session['user_id'] = user_id
        session['character_id'] = character_id
        
        # Log session data for debugging
        logger.info(f"Session data stored: {dict(session)}")
        
        # Update last played timestamp
        try:
            character.last_played = datetime.utcnow()
            
            # Save the updated timestamp
            if db is not None:
                db.characters.update_one(
                    {'character_id': character_id},
                    {'$set': {'last_played': datetime.utcnow()}}
                )
        except Exception as e:
            logger.warning(f"Error updating last_played timestamp: {e}")
        
        return render_template('dm.html', 
                             character=character_dict,
                             session_id=session.get('session_id'),
                             world_id=session.get('world_id'),
                             campaign_module_id=session.get('campaign_module_id'))
    
    except Exception as e:
        logger.error(f"Error in play_game route: {e}")
        import traceback
        logger.error(traceback.format_exc())
        flash('Error loading character: ' + str(e), 'error')
        return redirect(url_for('game.dashboard'))

@game_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_message():
    """Process a message from the player and return a DM response"""
    try:
        data = request.json
        player_message = data.get('message', '')  # Get player's message
        session_id = data.get('session_id')
        
        # Get IDs from Flask session (preferred) or request data (fallback)
        session_id = session.get('session_id') or data.get('session_id')
        character_id = session.get('character_id') or data.get('character_data', {}).get('character_id')
        user_id = session.get('user_id')
        world_id = session.get('world_id')
        campaign_module_id = session.get('campaign_module_id')

        # Validate required inputs
        if not player_message:
            return jsonify({
                'success': False,
                'error': 'No message provided'
            }), 400
            
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User not authenticated'
            }), 401
        
        if not character_id:
            return jsonify({
                'success': False,
                'error': 'No character selected'
            }), 400
            
        if not session_id:
        # If no session_id, something went wrong with session creation
            logger.error("No session_id found in Flask session or request data")
            return jsonify({
                'success': False,
                'error': 'No active game session'
            }), 400
        
        # Get the LangGraph manager
        manager = get_manager()
        
        # Process the message through LangGraph
        result = manager.process_message(
            session_id=session_id,
            message=player_message,
            character_id=character_id,
            user_id=user_id,
            world_id=world_id,
            campaign_module_id=campaign_module_id
        )
        
        # Process the LangGraph response
        if result.get('success'):
            # Extract the AI DM's response
            dm_response = result.get('response', 'The DM seems lost in thought...')
            
            # Prepare the success response dictionary
            response_data = {
                'dm_response': dm_response,
                'success': True
            }
            
            # Optional: Extract additional data from state if the frontend needs it
            if 'state' in result:
                state = result['state']
                
                # Extract game state
                game_state = state.get('game_state')
                if game_state:
                    response_data['game_state'] = game_state
                
                # Extract character stats
                tracked_narrative_state = state.get('tracked_narrative_state', {})
                character_stats = tracked_narrative_state.get('character_stats', {}).get(character_id)
                if character_stats:
                    response_data['character_stats'] = character_stats
                
                # Extract current location
                current_location = state.get('current_location_id')
                if current_location:
                    response_data['current_location'] = current_location
                
                # Extract pending checks or rolls
                pending_checks = tracked_narrative_state.get('pending_checks', [])
                pending_rolls = tracked_narrative_state.get('pending_rolls', [])
                if pending_checks or pending_rolls:
                    response_data['pending_actions'] = {
                        'checks': pending_checks,
                        'rolls': pending_rolls
                    }
            
            # Include session_id in response
            response_data['session_id'] = session_id
            
            return jsonify(response_data)
            
        else:
            # Processing failed - handle the error
            error = result.get('error', 'Unknown error')
            
            # Log the error server-side
            logger.error(f'LangGraph processing failed for session {session_id}: {error}')
            
            # Prepare an error response for the frontend
            response_data = {
                'dm_response': 'Sorry, the connection flickers. Could you repeat that?',
                'error': error,
                'success': False,
                'session_id': session_id
            }
            
            return jsonify(response_data), 500
        
    except Exception as e:
        logger.error(f"Unhandled exception in send_message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Prepare error response for unexpected exceptions
        response_data = {
            'dm_response': 'The magical energies waver momentarily. Please try again.',
            'error': f"Server error: {str(e)}",
            'success': False
        }
        
        return jsonify(response_data), 500

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
                'error': str(task.info or "Unknown task error")
            }
        elif task.state == 'SUCCESS':
            # Task completed successfully
            result = task.result
            
            # Ensure result has proper format
            if isinstance(result, dict) and 'response' in result:
                # Make sure response is not None
                if result['response'] is None:
                    result['response'] = "The Dungeon Master seems momentarily lost in thought."
                
                response = {
                    'success': True,
                    'status': 'completed',
                    'result': result
                }
            else:
                # Malformed result
                response = {
                    'success': False,
                    'status': 'error',
                    'error': 'Received malformed response from AI service'
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